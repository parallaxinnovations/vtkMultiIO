#include "vtkImageReader3.h"

#include "vtkByteSwap.h"
#include "vtkDataArray.h"
#include "vtkImageData.h"
#include "vtkInformation.h"
#include "vtkInformationVector.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"
#include "vtkErrorCode.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkStringArray.h"
#include "vtkType.h"

#include <sys/stat.h>

#include <fcntl.h>
#ifndef _WIN32
#include <unistd.h>
#else
#include <io.h>
#endif

vtkStandardNewMacro(vtkImageReader3);

/*
#ifdef read
#undef read
#endif

#ifdef close
#undef close
#endif
*/
//----------------------------------------------------------------------------
vtkImageReader3::vtkImageReader3()
{
  this->FilePrefix = NULL;
  this->FilePattern = new char[strlen("%s.%d") + 1];
  strcpy (this->FilePattern, "%s.%d");

  this->DataScalarType = VTK_SHORT;
  this->NumberOfScalarComponents = 1;
  this->Finalized = 0;
  this->DataOrigin[0] = this->DataOrigin[1] = this->DataOrigin[2] = 0.0;

  this->DataSpacing[0] = this->DataSpacing[1] = this->DataSpacing[2] = 1.0;

  this->DataExtent[0] = this->DataExtent[2] = this->DataExtent[4] = 0;
  this->DataExtent[1] = this->DataExtent[3] = this->DataExtent[5] = 0;

  this->DataIncrements[0] = this->DataIncrements[1] =
  this->DataIncrements[2] = this->DataIncrements[3] = 1;

  this->FileNames = NULL;

  this->FileName = NULL;
  this->InternalFileName = NULL;
  
  this->HeaderSize = 0;
  this->ManualHeaderSize = 0;
  
  this->FileNameSliceOffset = 0;
  this->FileNameSliceSpacing = 1;

  // Left over from short reader
  this->SwapBytes = 0;
  this->FileLowerLeft = 0;
  this->FileDimensionality = 2;
  this->SetNumberOfInputPorts(0);

  // Set file descriptor to -1
  this->fd = -1;

  this->MD5Sum = new char[32+1];
#ifdef _REQUIRE_CHECKSUMS_
  OpenSSL_add_all_digests();
  this->md = EVP_get_digestbyname("md5");
  this->md_len = 16;
#endif
}

//----------------------------------------------------------------------------
vtkImageReader3::~vtkImageReader3()
{

  delete [] this->MD5Sum;

  if (this->fd != -1)
    {
       close(fd);
       fd = -1;
    }

  if (this->FileNames)
    {
    this->FileNames->Delete();
    this->FileNames = NULL;
    }
  if (this->FileName)
    {
    delete [] this->FileName;
    this->FileName = NULL;
    }
  if (this->FilePrefix)
    {
    delete [] this->FilePrefix;
    this->FilePrefix = NULL;
    }
  if (this->FilePattern)
    {
    delete [] this->FilePattern;
    this->FilePattern = NULL;
    }
  if (this->InternalFileName)
    {
    delete [] this->InternalFileName;
    this->InternalFileName = NULL;
    }
}

//----------------------------------------------------------------------------
// This function sets the name of the file. 
void vtkImageReader3::ComputeInternalFileName(int slice)
{
  // delete any old filename
  if (this->InternalFileName)
    {
    delete [] this->InternalFileName;
    this->InternalFileName = NULL;
    }

  if (!this->FileName && !this->FilePattern && !this->FileNames)
    {
    vtkErrorMacro(<<"Either a FileName, FileNames, or FilePattern"
                  <<" must be specified.");
    return;
    }

  // make sure we figure out a filename to open
  if (this->FileNames)
    {
    const char *filename = this->FileNames->GetValue(slice);
    this->InternalFileName = new char [strlen(filename) + 10];
    sprintf(this->InternalFileName,"%s",filename);
    }
  else if (this->FileName)
    {
    this->InternalFileName = new char [strlen(this->FileName) + 10];
    sprintf(this->InternalFileName,"%s",this->FileName);
    }
  else
    {
    int slicenum =
      slice * this->FileNameSliceSpacing
      + this->FileNameSliceOffset;
    if (this->FilePrefix && this->FilePattern)
      {
      this->InternalFileName = new char [strlen(this->FilePrefix) +
                                        strlen(this->FilePattern) + 10];
      sprintf (this->InternalFileName, this->FilePattern,
               this->FilePrefix, slicenum);
      }
    else if (this->FilePattern)
      {
      this->InternalFileName = new char [strlen(this->FilePattern) + 10];
      int len = static_cast<int>(strlen(this->FilePattern));
      int hasPercentS = 0;
      for(int i =0; i < len-1; ++i)
        {
        if(this->FilePattern[i] == '%' && this->FilePattern[i+1] == 's')
          {
          hasPercentS = 1;
          break;
          }
        }
      if(hasPercentS)
        {
        sprintf (this->InternalFileName, this->FilePattern, "", slicenum);
        }
      else
        {
        sprintf (this->InternalFileName, this->FilePattern, slicenum);
        }
      }
    else
      {
      delete [] this->InternalFileName;
      this->InternalFileName = 0;
      }
    }
}


//----------------------------------------------------------------------------
// This function sets the name of the file. 
void vtkImageReader3::SetFileName(const char *name)
{
  if ( this->FileName && name && (!strcmp(this->FileName,name)))
    {
    return;
    }
  if (!name && !this->FileName)
    {
    return;
    }
  if (this->FileName)
    {
    delete [] this->FileName;
    this->FileName = NULL;
    }
  if (name)
    {
    this->FileName = new char[strlen(name) + 1];
    strcpy(this->FileName, name);

    if (this->FilePrefix)
      {
      delete [] this->FilePrefix;
      this->FilePrefix = NULL;
      }
    if (this->FileNames)
      {
      this->FileNames->Delete();
      this->FileNames = NULL;
      }
  // set up md5sum structures
#ifdef _REQUIRE_CHECKSUMS_
  EVP_MD_CTX_init(&mdctx);
  EVP_DigestInit_ex(&mdctx, md, NULL);
#endif
  this->Finalized = 0;
  this->Modified();
}
}

char *vtkImageReader3::GetMD5Sum(void)
{

  // do we need to finalize our checksum?
  if (this->Finalized == 0)
      this->FinalizeDigest();
  return this->MD5Sum;
}


//----------------------------------------------------------------------------
// This function sets an array containing file names 
void vtkImageReader3::SetFileNames(vtkStringArray *filenames)
{
  if (filenames == this->FileNames)
    {
    return;
    }
  if (this->FileNames)
    {
    this->FileNames->Delete();
    this->FileNames = 0;
    }
  if (filenames)
    {
    this->FileNames = filenames;
    this->FileNames->Register(this);
    if (this->FileNames->GetNumberOfValues() > 0)
      {
      this->DataExtent[4] = 0;
      this->DataExtent[5] = this->FileNames->GetNumberOfValues() - 1;
      }
    if (this->FilePrefix)
      {
      delete [] this->FilePrefix;
      this->FilePrefix = NULL;
      }
    if (this->FileName)
      {
      delete [] this->FileName;
      this->FileName = NULL;
      }
    }

  this->Modified();
}

//----------------------------------------------------------------------------
// This function sets the prefix of the file name. "image" would be the
// name of a series: image.1, image.2 ...
void vtkImageReader3::SetFilePrefix(const char *prefix)
{
  if ( this->FilePrefix && prefix && (!strcmp(this->FilePrefix,prefix)))
    {
    return;
    }
  if (!prefix && !this->FilePrefix)
    {
    return;
    }
  if (this->FilePrefix)
    {
    delete [] this->FilePrefix;
    this->FilePrefix = NULL;
    }
  if (prefix)
    {
    this->FilePrefix = new char[strlen(prefix) + 1];
    strcpy(this->FilePrefix, prefix);

    if (this->FileName)
      {
      delete [] this->FileName;
      this->FileName = NULL;
      }
    if (this->FileNames)
      {
      this->FileNames->Delete();
      this->FileNames = NULL;
      }
    }

  // set up md5sum structures
#ifdef _REQUIRE_CHECKSUMS_
  EVP_MD_CTX_init(&mdctx);
  EVP_DigestInit_ex(&mdctx, md, NULL);
#endif

  this->Modified();
}

//----------------------------------------------------------------------------
// This function sets the pattern of the file name which turn a prefix
// into a file name. "%s.%03d" would be the
// pattern of a series: image.001, image.002 ...
void vtkImageReader3::SetFilePattern(const char *pattern)
{
  if ( this->FilePattern && pattern &&
       (!strcmp(this->FilePattern,pattern)))
    {
    return;
    }
  if (!pattern && !this->FilePattern)
    {
    return;
    }
  if (this->FilePattern)
    {
    delete [] this->FilePattern;
    this->FilePattern = NULL;
    }
  if (pattern)
    {
    this->FilePattern = new char[strlen(pattern) + 1];
    strcpy(this->FilePattern, pattern);

    if (this->FileName)
      {
      delete [] this->FileName;
      this->FileName = NULL;
      }
    if (this->FileNames)
      {
      this->FileNames->Delete();
      this->FileNames = NULL;
      }
    }

  this->Modified();
}

//----------------------------------------------------------------------------
void vtkImageReader3::SetDataByteOrderToBigEndian()
{
#ifndef VTK_WORDS_BIGENDIAN
  this->SwapBytesOn();
#else
  this->SwapBytesOff();
#endif
}

//----------------------------------------------------------------------------
void vtkImageReader3::SetDataByteOrderToLittleEndian()
{
#ifdef VTK_WORDS_BIGENDIAN
  this->SwapBytesOn();
#else
  this->SwapBytesOff();
#endif
}

//----------------------------------------------------------------------------
void vtkImageReader3::SetDataByteOrder(int byteOrder)
{
  if ( byteOrder == VTK_FILE_BYTE_ORDER_BIG_ENDIAN )
    {
    this->SetDataByteOrderToBigEndian();
    }
  else
    {
    this->SetDataByteOrderToLittleEndian();
    }
}

//----------------------------------------------------------------------------
int vtkImageReader3::GetDataByteOrder()
{
#ifdef VTK_WORDS_BIGENDIAN
  if ( this->SwapBytes )
    {
    return VTK_FILE_BYTE_ORDER_LITTLE_ENDIAN;
    }
  else
    {
    return VTK_FILE_BYTE_ORDER_BIG_ENDIAN;
    }
#else
  if ( this->SwapBytes )
    {
    return VTK_FILE_BYTE_ORDER_BIG_ENDIAN;
    }
  else
    {
    return VTK_FILE_BYTE_ORDER_LITTLE_ENDIAN;
    }
#endif
}

//----------------------------------------------------------------------------
const char *vtkImageReader3::GetDataByteOrderAsString()
{
#ifdef VTK_WORDS_BIGENDIAN
  if ( this->SwapBytes )
    {
    return "LittleEndian";
    }
  else
    {
    return "BigEndian";
    }
#else
  if ( this->SwapBytes )
    {
    return "BigEndian";
    }
  else
    {
    return "LittleEndian";
    }
#endif
}


//----------------------------------------------------------------------------
void vtkImageReader3::PrintSelf(ostream& os, vtkIndent indent)
{
  int idx;

  this->Superclass::PrintSelf(os,indent);

  // this->File, this->Colors need not be printed
  os << indent << "FileName: " <<
    (this->FileName ? this->FileName : "(none)") << "\n";
  os << indent << "FileNames: " << this->FileNames << "\n";
  os << indent << "FilePrefix: " <<
    (this->FilePrefix ? this->FilePrefix : "(none)") << "\n";
  os << indent << "FilePattern: " <<
    (this->FilePattern ? this->FilePattern : "(none)") << "\n";

  os << indent << "FileNameSliceOffset: "
     << this->FileNameSliceOffset << "\n";
  os << indent << "FileNameSliceSpacing: "
     << this->FileNameSliceSpacing << "\n";

  os << indent << "DataScalarType: "
     << vtkImageScalarTypeNameMacro(this->DataScalarType) << "\n";
  os << indent << "NumberOfScalarComponents: "
     << this->NumberOfScalarComponents << "\n";

  os << indent << "File Dimensionality: " << this->FileDimensionality << "\n";

  os << indent << "File Lower Left: " <<
    (this->FileLowerLeft ? "On\n" : "Off\n");

  os << indent << "Swap Bytes: " << (this->SwapBytes ? "On\n" : "Off\n");

  os << indent << "DataIncrements: (" << this->DataIncrements[0];
  for (idx = 1; idx < 2; ++idx)
    {
    os << ", " << this->DataIncrements[idx];
    }
  os << ")\n";

  os << indent << "DataExtent: (" << this->DataExtent[0];
  for (idx = 1; idx < 6; ++idx)
    {
    os << ", " << this->DataExtent[idx];
    }
  os << ")\n";

  os << indent << "DataSpacing: (" << this->DataSpacing[0];
  for (idx = 1; idx < 3; ++idx)
    {
    os << ", " << this->DataSpacing[idx];
    }
  os << ")\n";

  os << indent << "DataOrigin: (" << this->DataOrigin[0];
  for (idx = 1; idx < 3; ++idx)
    {
    os << ", " << this->DataOrigin[idx];
    }
  os << ")\n";

  os << indent << "HeaderSize: " << this->HeaderSize << "\n";

  if ( this->InternalFileName )
    {
    os << indent << "Internal File Name: " << this->InternalFileName << "\n";
    }
  else
    {
    os << indent << "Internal File Name: (none)\n";
    }
}

//----------------------------------------------------------------------------
void vtkImageReader3::ExecuteInformation()
{
  // this is empty, the idea is that converted filters should implement
  // RequestInformation. But to help out old filters we will call
  // ExecuteInformation and hope that the subclasses correctly set the ivars
  // and not the output.
}

//----------------------------------------------------------------------------
// This method returns the largest data that can be generated.
int vtkImageReader3::RequestInformation (
  vtkInformation       * vtkNotUsed( request ),
  vtkInformationVector** vtkNotUsed( inputVector ),
  vtkInformationVector * outputVector)
{
  this->SetErrorCode( vtkErrorCode::NoError );
  // call for backwards compatibility
  this->ExecuteInformation();
  // Check for any error set by downstream filter (IO in most case)
  if ( this->GetErrorCode() )
    {
    return 0;
    }

  // get the info objects
  vtkInformation* outInfo = outputVector->GetInformationObject(0);

  // if a list of file names is supplied, set slice extent
  if (this->FileNames && this->FileNames->GetNumberOfValues() > 0)
    {
    this->DataExtent[4] = 0;
    this->DataExtent[5] = this->FileNames->GetNumberOfValues()-1;
    }

  outInfo->Set(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(),
               this->DataExtent, 6);
  outInfo->Set(vtkDataObject::SPACING(), this->DataSpacing, 3);
  outInfo->Set(vtkDataObject::ORIGIN(),  this->DataOrigin, 3);

  vtkDataObject::SetPointDataActiveScalarInfo(outInfo, this->DataScalarType,
    this->NumberOfScalarComponents);
  return 1;
}

//----------------------------------------------------------------------------
// Manual initialization.
void vtkImageReader3::SetHeaderSize(unsigned long size)
{
  if (size != this->HeaderSize)
    {
    this->HeaderSize = size;
    this->Modified();
    }
  this->ManualHeaderSize = 1;
}


//----------------------------------------------------------------------------
template <class T>
unsigned long vtkImageReader3GetSize(T*)
{
  return sizeof(T);
}

//----------------------------------------------------------------------------
// This function opens a file to determine the file size, and to
// automatically determine the header size.
void vtkImageReader3::ComputeDataIncrements()
{
  int idx;
  vtkTypeUInt64 fileDataLength;

  // Determine the expected length of the data ...
  switch (this->DataScalarType)
    {
    vtkTemplateMacro(
      fileDataLength = vtkImageReader3GetSize(static_cast<VTK_TT*>(0))
      );
    default:
      vtkErrorMacro(<< "Unknown DataScalarType");
      return;
    }

  fileDataLength *= this->NumberOfScalarComponents;
  
  // compute the fileDataLength (in units of bytes)
  for (idx = 0; idx < 3; ++idx)
    {
    this->DataIncrements[idx] = fileDataLength;
    fileDataLength = fileDataLength *
      (this->DataExtent[idx*2+1] - this->DataExtent[idx*2] + 1);
    }
  this->DataIncrements[3] = fileDataLength;
}


//----------------------------------------------------------------------------
int vtkImageReader3::OpenFile()
{
  if (!this->FileName && !this->FilePattern)
    {
    vtkErrorMacro(<<"Either a FileName, FileNames, or FilePattern"
                  << " must be specified.");
    return 0;
    }

  // Close file from any previous image
  if (this->fd != -1)
    {
    close(this->fd);
    this->fd = -1;
    }

  // Open the new file
  vtkDebugMacro(<< "Initialize: opening file " << this->InternalFileName);

#ifdef _WIN32
  struct _stat64  fs;
  if ( !_stat64( this->InternalFileName, &fs) )
    {
    this->fd = _open(this->InternalFileName, O_RDONLY | O_BINARY);
    }
#else
  struct stat fs;
  if ( !stat( this->InternalFileName, &fs) )
    {
    this->fd = open(this->InternalFileName, O_RDONLY);
    }
#endif

  if (fd < 0)
    {
    vtkErrorMacro(<< "Initialize: Could not open file "
                  << this->InternalFileName);
    return 0;
    }
  return 1;
}


//----------------------------------------------------------------------------
unsigned long vtkImageReader3::GetHeaderSize()
{
  unsigned long firstIdx;

  if (this->FileNames)
    {
    // if FileNames is used, indexing always starts at zero
    firstIdx = 0;
    }
  else
    {
    // FilePrefix uses the DataExtent to figure out the first slice index
    firstIdx = this->DataExtent[4];
    }

  return this->GetHeaderSize(firstIdx);
}

//----------------------------------------------------------------------------
unsigned long vtkImageReader3::GetHeaderSize(unsigned long idx)
{
  if (!this->FileName && !this->FilePattern)
    {
    vtkErrorMacro(<<"Either a FileName or FilePattern must be specified.");
    return 0;
    }
  if ( ! this->ManualHeaderSize)
    {
    this->ComputeDataIncrements();

    // make sure we figure out a filename to open
    this->ComputeInternalFileName(idx);

    struct stat statbuf;
    if (!stat(this->InternalFileName, &statbuf))
      {
      return (int)(statbuf.st_size -
                   (long)this->DataIncrements[this->GetFileDimensionality()]);
      }
    }

  return this->HeaderSize;
}

//----------------------------------------------------------------------------
void vtkImageReader3::SeekFile(int i, int j, int k)
{
  vtkTypeUInt64 streamStart;

  // convert data extent into constants that can be used to seek.
  streamStart =
    (i - this->DataExtent[0]) * this->DataIncrements[0];

  if (this->FileLowerLeft)
    {
    streamStart = streamStart +
      (j - this->DataExtent[2]) * this->DataIncrements[1];
    }
  else
    {
    streamStart = streamStart +
      (this->DataExtent[3] - this->DataExtent[2] - j) *
      this->DataIncrements[1];
    }

  // handle three and four dimensional files
  if (this->GetFileDimensionality() >= 3)
    {
    streamStart = streamStart +
      (k - this->DataExtent[4]) * this->DataIncrements[2];
    }

  streamStart += this->GetHeaderSize(k);

  // error checking
  if (this->fd < 0)
    {
    vtkWarningMacro(<<"File must be specified.");
    return;
    }

  if (lseek(this->fd, (off_t)streamStart, SEEK_SET) != streamStart)
    {
    vtkWarningMacro("File operation failed.");
    return;
    }
}

//----------------------------------------------------------------------------
// This function reads in one data of data.
// templated to handle different data types.
template <class OT>
#ifdef _REQUIRE_CHECKSUMS_
void vtkImageReader3Update(vtkImageReader3 *self, vtkImageData *data, OT *outPtr, EVP_MD_CTX * mdctx)
#else
void vtkImageReader3Update(vtkImageReader3 *self, vtkImageData *data, OT *outPtr)
#endif
{
  vtkIdType outIncr[3];
  OT *outPtr1;
  long streamRead;
  int idx1 = 0, idx2, nComponents;
  int outExtent[6];
  unsigned long count = 0, numZ;
  
  // Get the requested extents and increments
  data->GetExtent(outExtent);
  data->GetIncrements(outIncr);
  nComponents = data->GetNumberOfScalarComponents();
  
  // length of a slice, num pixels read at a time
  int pixelRead = (outExtent[1] - outExtent[0] + 1) * (outExtent[3] - outExtent[2] + 1);
  streamRead = (long)(pixelRead*nComponents*sizeof(OT));  

  // number of Z slices
  numZ = outExtent[5] - outExtent[4] + 1;
  
  // read the data row by row
  if (self->GetFileDimensionality() == 3)
    {
    self->ComputeInternalFileName(0);
    if ( !self->OpenFile() )
      {
      return;
      }
    }
  outPtr1 = outPtr;

  // seek to the correct row
  lseek(self->GetFd(), self->GetHeaderSize(), SEEK_SET);

  for (idx2 = outExtent[4]; idx2 <= outExtent[5]; ++idx2)
    {
    if (self->GetFileDimensionality() == 2)
      {
      vtkGenericWarningMacro("File operations on 2D image not supported!!\n");
      self->ComputeInternalFileName(idx2);
      if ( !self->OpenFile() )
        {
        return;
        }
      }
    self->UpdateProgress((float)count/(float)numZ);
    count++;

    // read the slice
    if ( !read(self->GetFd(), (char *)outPtr1, streamRead))
        {
        vtkGenericWarningMacro("File operation failed. slice = " << idx1
                               << ", Read = " << streamRead
                               << ", FilePos = " << lseek(self->GetFd(), 0, SEEK_CUR));
        return;
        }

      // update digest
#ifdef _REQUIRE_CHECKSUMS_
      EVP_DigestUpdate(mdctx, outPtr1, streamRead);
#endif

      // handle swapping
      if (self->GetSwapBytes() && sizeof(OT) > 1)
        {
        vtkByteSwap::SwapVoidRange(outPtr1, pixelRead*nComponents, sizeof(OT));
        }

      // handle image flip
	  if (self->GetFileLowerLeft() == 1) {
      
        long num_x = (outExtent[1] - outExtent[0] + 1) * nComponents;
        long num_y = (outExtent[3] - outExtent[2] + 1);

        OT temp;
        OT *flip1, *flip2;

#pragma omp parallel
        for (long y = 0; y < (num_y / 2); y++) {
            flip1 = &outPtr1[y * num_x * nComponents];
            flip2 = &outPtr1[(num_y - y - 1) * num_x * nComponents];
            for (long x = 0; x < num_x; x++) {
                temp = flip1[x];
                flip1[x] = flip2[x];
                flip2[x] = temp;
            }
        }
      }

    // increment
    outPtr1 += outIncr[2];
    }
}

void vtkImageReader3::FinalizeDigest()
{
    this->Finalized = 1;

#ifdef _REQUIRE_CHECKSUMS_
    EVP_DigestFinal_ex(&mdctx, md_value, &md_len);
    EVP_MD_CTX_cleanup(&mdctx);

    char *p = MD5Sum;

    int i;

    // write digest value
    for (i = 0; i < md_len; i++) {
      sprintf(p, "%02x", md_value[i]);
      p++; p++;
    }
#endif
}

//----------------------------------------------------------------------------
// This function reads a data from a file.  The datas extent/axes
// are assumed to be the same as the file extent/order.
void vtkImageReader3::ExecuteDataWithInformation(vtkDataObject *output,
                                                 vtkInformation *outInfo)
{
  vtkImageData *data = this->AllocateOutputData(output, outInfo);

  void *ptr;

  if (!this->FileName && !this->FilePattern)
    {
    vtkErrorMacro("Either a valid FileName or FilePattern must be specified.");
    return;
    }

  data->GetPointData()->GetScalars()->SetName("ImageFile");

#ifndef NDEBUG
  int *ext = data->GetExtent();
#endif

  vtkDebugMacro("Reading extent: " << ext[0] << ", " << ext[1] << ", "
        << ext[2] << ", " << ext[3] << ", " << ext[4] << ", " << ext[5]);

  this->ComputeDataIncrements();

  // Call the correct templated function for the output
  ptr = data->GetScalarPointer();
  switch (this->GetDataScalarType())
    {
#ifdef _REQUIRE_CHECKSUMS_
    vtkTemplateMacro(vtkImageReader3Update(this, data, (VTK_TT *)(ptr), &mdctx));
#else
    vtkTemplateMacro(vtkImageReader3Update(this, data, (VTK_TT *)(ptr)));
#endif
    default:
      vtkErrorMacro(<< "UpdateFromFile: Unknown data type");
    }
}


//----------------------------------------------------------------------------
// Set the data type of pixels in the file.
// If you want the output scalar type to have a different value, set it
// after this method is called.
void vtkImageReader3::SetDataScalarType(int type)
{
  if (type == this->DataScalarType)
    {
    return;
    }

  this->Modified();
  this->DataScalarType = type;
  // Set the default output scalar type
  vtkImageData::SetScalarType(this->DataScalarType,
                              this->GetOutputInformation(0));
}
void vtkImageReader3::GetScalarRange(float range[2])
{
   void *ptr;
   float *fptr;
   short *iptr;
   long count, i; 
   unsigned char *uptr;
   
   count = (this->DataExtent[1] - this->DataExtent[0] + 1) *
           (this->DataExtent[3] - this->DataExtent[2] + 1) *
           (this->DataExtent[5] - this->DataExtent[4] + 1);
   
   range[0] = VTK_FLOAT_MAX;
   range[1] = -VTK_FLOAT_MAX;
   ptr = this->GetOutput()->GetScalarPointer();

   switch (this->DataScalarType) 
     {
	case VTK_FLOAT:
	fptr = (float *) ptr;
 	for (i = 0; i < count; i++) 
	  { 
	     if (range[0] > fptr[i])
	       range[0] = fptr[i];
	     if (range[1] < fptr[i])
	       range[1] = fptr[i];
	  }
	break;
	case VTK_SHORT:
	iptr = (short *) ptr;
 	for (i = 0; i < count; i++) 
	  { 
	     if (range[0] > iptr[i])
	       range[0] = iptr[i];
	     if (range[1] < iptr[i])
	       range[1] = iptr[i];
	  }
	break;
	case VTK_UNSIGNED_CHAR:
	uptr = (unsigned char *) ptr;
 	for (i = 0; i < count; i++) 
	  { 
	     if (range[0] > uptr[i])
	       range[0] = uptr[i];
	     if (range[1] < uptr[i])
	       range[1] = uptr[i];	  }
	break;
     }
}

  
