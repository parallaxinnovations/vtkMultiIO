#include "vtkVFFWriter.h"

#include "vtkCommand.h"
#include "vtkErrorCode.h"
#include "vtkInformation.h"
#include "vtkInformationExecutivePortKey.h"
#include "vtkInformationVector.h"
#include "vtkObjectFactory.h"
#include "vtkPointData.h"
#include "vtkStreamingDemandDrivenPipeline.h"
#include "vtkImageData.h"

#include <vtksys/SystemTools.hxx>

vtkStandardNewMacro(vtkVFFWriter);


#include "vtkByteSwap.h"
#include <iomanip>

#ifndef WIN32
#include <unistd.h>
#endif

//--------------------------------------------------------------------------
vtkVFFWriter::vtkVFFWriter()
{
  this->FilePrefix = NULL;
  this->FilePattern = NULL;
  this->FileName = NULL;
  this->InternalFileName = NULL;
  this->FileNumber = 0;
  this->FileDimensionality = 3;

  this->FilePattern = new char[strlen("%s.%d") + 1];
  strcpy(this->FilePattern, "%s.%d");

  this->FileLowerLeft = 1;

  this->MinimumFileNumber = this->MaximumFileNumber = 0;
  this->FilesDeleted = 0;
  this->SetNumberOfOutputPorts(0);

#ifdef _REQUIRE_CHECKSUMS_
  OpenSSL_add_all_digests();
  this->md = EVP_get_digestbyname(DIGEST_TYPE);
  this->md_len = 16;
#endif
}



//----------------------------------------------------------------------------
vtkVFFWriter::~vtkVFFWriter()
{
  // get rid of memory allocated for file names
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
  if (this->FileName)
    {
    delete [] this->FileName;
    this->FileName = NULL;
    }
}


//----------------------------------------------------------------------------
void vtkVFFWriter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "FileName: " <<
    (this->FileName ? this->FileName : "(none)") << "\n";
  os << indent << "FilePrefix: " <<
    (this->FilePrefix ? this->FilePrefix : "(none)") << "\n";
  os << indent << "FilePattern: " <<
    (this->FilePattern ? this->FilePattern : "(none)") << "\n";

  os << indent << "FileDimensionality: " << this->FileDimensionality << "\n";

  // print header values
  std::map<vtkStdString, vtkStdString>::iterator curr;
  curr = this->header.header.begin();
  os << indent << "Header Keywords:\n";  
  for (vtkstd::map<vtkStdString, vtkStdString>::iterator i = this->header.header.begin();
       i != this->header.header.end(); ++i)
    os << indent << indent << i->first << ": " << i->second << "\n";
}

//----------------------------------------------------------------------------
// Breaks region into pieces with correct dimensionality.
void vtkVFFWriter::RecursiveWrite(int axis,
                                    vtkImageData *cache,
                                    vtkInformation* inInfo,
                                    ofstream *file)
{
  vtkImageData    *data;
  int             fileOpenedHere = 0;

  // if we need to open another slice, do it
  if (!file && (axis + 1) == this->FileDimensionality)
    {
    // determine the name
    if (this->FileName)
      {
      sprintf(this->InternalFileName,"%s",this->FileName);
      }
    else
      {
      if (this->FilePrefix)
        {
        sprintf(this->InternalFileName, this->FilePattern,
                this->FilePrefix, this->FileNumber);
        }
      else
        {
        sprintf(this->InternalFileName, this->FilePattern,this->FileNumber);
        }
      if (this->FileNumber < this->MinimumFileNumber)
        {
        this->MinimumFileNumber = this->FileNumber;
        }
      else if (this->FileNumber > this->MaximumFileNumber)
        {
        this->MaximumFileNumber = this->FileNumber;
        }
      }
    // Open the file
#ifdef _WIN32
    file = new ofstream(this->InternalFileName, ios::out | ios::binary);
#else
    file = new ofstream(this->InternalFileName, ios::out);
#endif
    fileOpenedHere = 1;
    if (file->fail())
      {
      vtkErrorMacro("RecursiveWrite: Could not open file " <<
                    this->InternalFileName);
      this->SetErrorCode(vtkErrorCode::CannotOpenFileError);
      delete file;
      return;
      }

    // Subclasses can write a header with this method call.
    int* wExt = vtkStreamingDemandDrivenPipeline::GetWholeExtent(inInfo);
    this->WriteFileHeader(file, cache, wExt);
    file->flush();
    if (file->fail())
      {
      file->close();
      delete file;
      this->SetErrorCode(vtkErrorCode::OutOfDiskSpaceError);
      return;
      }
    ++this->FileNumber;
    }

  // Propagate the update extent so we can determine pipeline size
  vtkStreamingDemandDrivenPipeline* inputExec =
    vtkStreamingDemandDrivenPipeline::SafeDownCast(
      vtkExecutive::PRODUCER()->GetExecutive(inInfo));
  int inputOutputPort = vtkExecutive::PRODUCER()->GetPort(inInfo);
  inputExec->PropagateUpdateExtent(inputOutputPort);

  // just get the data and write it out
#ifndef NDEBUG
  int *ext = vtkStreamingDemandDrivenPipeline::GetUpdateExtent(inInfo);
#endif
  vtkDebugMacro("Getting input extent: " << ext[0] << ", " <<
                ext[1] << ", " << ext[2] << ", " << ext[3] << ", " <<
                ext[4] << ", " << ext[5] << endl);
  inputExec->Update(inputOutputPort);
  data = cache;
  this->RecursiveWrite(axis,cache,data,inInfo,file);
  if (this->ErrorCode == vtkErrorCode::OutOfDiskSpaceError)
    {
    this->DeleteFiles();
    return;
    }
  if (file && fileOpenedHere)
    {
    this->WriteFileTrailer(file,cache);
    file->flush();
    if (file->fail())
      {
      this->SetErrorCode(vtkErrorCode::OutOfDiskSpaceError);
      }

    // finalize md5 checksum
#ifdef _REQUIRE_CHECKSUMS_
    // finalize md5 checksum
    EVP_DigestFinal_ex(&mdctx, md_value, &md_len);
    EVP_MD_CTX_cleanup(&mdctx);

    char *hexdigest = new char[md_len*2+1];
    char *p = hexdigest;

    int i;

    //seek back to correct location
    file->seekp(fposition);

    // write digest value - this works but ask Del for help here
    for (i = 0; i < md_len; i++) {
      sprintf(p, "%02x", md_value[i]);
      p++; p++;
    }
    *file << hexdigest;
    delete [] hexdigest;
#endif
    file->close();
    delete file;
    }
  return;
}


//----------------------------------------------------------------------------
// same idea as the previous method, but it knows that the data is ready
void vtkVFFWriter::RecursiveWrite(int axis,
                                    vtkImageData *cache,
                                    vtkImageData *data,
                                    vtkInformation* inInfo,
                                    ofstream *file)
{
  int idx, min, max;

  int* wExt = vtkStreamingDemandDrivenPipeline::GetWholeExtent(inInfo);
  // if the file is already open then just write to it
  if (file)
    {
    this->WriteFile(file,data,
                    vtkStreamingDemandDrivenPipeline::GetUpdateExtent(inInfo),
                    wExt);
    file->flush();
    if (file->fail())
      {
      file->close();
      delete file;
      this->SetErrorCode(vtkErrorCode::OutOfDiskSpaceError);
      }
    return;
    }

  // if we need to open another slice, do it
  if (!file && (axis + 1) == this->FileDimensionality)
    {
    // determine the name
    if (this->FileName)
      {
      sprintf(this->InternalFileName,"%s",this->FileName);
      }
    else
      {
      if (this->FilePrefix)
        {
        sprintf(this->InternalFileName, this->FilePattern,
                this->FilePrefix, this->FileNumber);
        }
      else
        {
        sprintf(this->InternalFileName, this->FilePattern,this->FileNumber);
        }
      if (this->FileNumber < this->MinimumFileNumber)
        {
        this->MinimumFileNumber = this->FileNumber;
        }
      else if (this->FileNumber > this->MaximumFileNumber)
        {
        this->MaximumFileNumber = this->FileNumber;
        }
      }
    // Open the file
#ifdef _WIN32
    file = new ofstream(this->InternalFileName, ios::out | ios::binary);
#else
    file = new ofstream(this->InternalFileName, ios::out);
#endif
    if (file->fail())
      {
      vtkErrorMacro("RecursiveWrite: Could not open file " <<
                    this->InternalFileName);
      this->SetErrorCode(vtkErrorCode::CannotOpenFileError);
      delete file;
      return;
      }

    // Subclasses can write a header with this method call.
    this->WriteFileHeader(file, cache, wExt);
    file->flush();
    if (file->fail())
      {
      file->close();
      delete file;
      this->SetErrorCode(vtkErrorCode::OutOfDiskSpaceError);
      return;
      }
    this->WriteFile(file,data,vtkStreamingDemandDrivenPipeline::GetUpdateExtent(inInfo),wExt);
    file->flush();
    if (file->fail())
      {
      file->close();
      delete file;
      this->SetErrorCode(vtkErrorCode::OutOfDiskSpaceError);
      return;
      }
    ++this->FileNumber;
    this->WriteFileTrailer(file,cache);
    file->flush();
    if (file->fail())
      {
      this->SetErrorCode(vtkErrorCode::OutOfDiskSpaceError);
      }
    // optionally write checksum here
#ifdef _REQUIRE_CHECKSUMS_
    // finalize md5 checksum
    EVP_DigestFinal_ex(&mdctx, md_value, &md_len);
    EVP_MD_CTX_cleanup(&mdctx);

    char *hexdigest = new char[md_len*2+1];
    char *p = hexdigest;

    int i;

    //seek back to correct location
    file->seekp(fposition);

    // write digest value - this works but ask Del for help here
    for (i = 0; i < md_len; i++) {
      sprintf(p, "%02x", md_value[i]);
      p++; p++;
    }
    *file << hexdigest;
    delete [] hexdigest;

#endif
    file->close();
    delete file;
    return;
    }

  // if the current region is too high a dimension forthe file
  // the we will split the current axis
  int* updateExtent = vtkStreamingDemandDrivenPipeline::GetUpdateExtent(inInfo);
  cache->GetAxisUpdateExtent(axis, min, max,
                             updateExtent);

  int axisUpdateExtent[6];
  // if it is the y axis then flip by default
  if (axis == 1 && !this->FileLowerLeft)
    {
    for(idx = max; idx >= min; idx--)
      {
      cache->SetAxisUpdateExtent(axis, idx, idx, updateExtent, axisUpdateExtent);
      vtkStreamingDemandDrivenPipeline::SetUpdateExtent(inInfo, axisUpdateExtent);
      if (this->ErrorCode != vtkErrorCode::OutOfDiskSpaceError)
        {
        this->RecursiveWrite(axis - 1, cache, data, inInfo, file);
        }
      else
        {
        this->DeleteFiles();
        }
      }
    }
  else
    {
    for(idx = min; idx <= max; idx++)
      {
      cache->SetAxisUpdateExtent(axis, idx, idx, updateExtent, axisUpdateExtent);
      vtkStreamingDemandDrivenPipeline::SetUpdateExtent(inInfo, axisUpdateExtent);
      if (this->ErrorCode != vtkErrorCode::OutOfDiskSpaceError)
        {
        this->RecursiveWrite(axis - 1, cache, data, inInfo, file);
        }
      else
        {
        this->DeleteFiles();
        }
      }
    }

  // restore original extent
  cache->SetAxisUpdateExtent(axis, min, max, updateExtent, axisUpdateExtent);
  vtkStreamingDemandDrivenPipeline::SetUpdateExtent(inInfo, axisUpdateExtent);
}


//----------------------------------------------------------------------------
template <class T>
unsigned long vtkImageWriterGetSize(T*)
{
  return sizeof(T);
}

//----------------------------------------------------------------------------
void vtkVFFWriter::WriteFileHeader(ofstream *file, vtkImageData *cache, int wExt[6])
{
  int width, height, depth, dimensionality = 0, rawsize;
  double *spacing, *origin;
  double o2;

  // we need to know something about the update extent
  vtkInformation* inInfo = this->GetInputInformation(0, 0);
  int *ext = vtkStreamingDemandDrivenPipeline::GetUpdateExtent(inInfo);

  // Find the length of the rows to write.
  width = (wExt[1] - wExt[0] + 1);
  height = (wExt[3] - wExt[2] + 1);
  depth = (wExt[5] - wExt[4] + 1);
  
  // work out effective dimensionality
  if (width > 1)
    dimensionality++;
  if (height > 1)
    dimensionality++;
  if (depth > 1)
    dimensionality++;
 
  // rawsize
  rawsize = width * height * depth * cache->GetScalarSize() * cache->GetNumberOfScalarComponents();
  
  // Get image spacing & origin
  spacing = cache->GetSpacing();
  origin = cache->GetOrigin();
 
  // adjust origin, as needed
  o2 = origin[2];
  o2 += (spacing[2] * (ext[2] - (wExt[4] - wExt[3])));
  
  // spit out the VFF header
  *file << "ncaa\n";
  *file << "type=raster;\n";
  *file << "format=slice;\n";
  *file << "bands=" << cache->GetNumberOfScalarComponents() << ";\n";
  *file << "rank=" << dimensionality << ";\n"; 
  *file << "bits=" << cache->GetScalarSize()*8 << ";\n";
  *file << "size=" << width << " " << height;
  if (dimensionality > 2)
    *file << " " << depth;
  *file << ";\n";
  *file << "rawsize=" << rawsize << ";\n";
  *file << "origin=" << (origin[0]/spacing[0]) << " " << (origin[1]/spacing[1]);
  if (dimensionality > 2)
    *file << " " << (o2/spacing[2]);
  *file << ";\n";
  *file << "spacing=" << spacing[0] << " " << spacing[1];
  if (dimensionality > 2)
    *file << " " << spacing[2];
  *file << ";\n";


  // optionally add/modify an image md5sum value
#ifdef _REQUIRE_CHECKSUMS_

  vtkstd::string checksum_key, checksum_value;

  // check for image_type keyword - set a sensible default if missing
  if (strlen(this->GetKeyword("image_type")) == 0)
    this->SetKeyword("image_type","image");

  // get image type
  checksum_key += this->GetKeyword("image_type");

  checksum_key += "_";
  checksum_key += DIGEST_TYPE;
  checksum_key += "_digest";

  // create a dummy checksum
  for (int i = 0; i < md_len*2; i++)
    checksum_value += "X";

  // add it as a record
  this->SetKeyword(checksum_key.c_str(), checksum_value.c_str());

  // set up md5sum structures
  EVP_MD_CTX_init(&mdctx);
  EVP_DigestInit_ex(&mdctx, md, NULL);
#endif

  // print additional header keywords
  vtkstd::map<vtkStdString, vtkStdString>::iterator curr;
  curr = this->header.header.begin();
  for (vtkstd::map<vtkStdString, vtkStdString>::iterator i = this->header.header.begin();
       i != this->header.header.end(); ++i) {

#ifdef _REQUIRE_CHECKSUMS_
  // remember what line our checksum is on
  if (i->first == checksum_key) {
    fposition = file->tellp();
    fposition += strlen(checksum_key.c_str());
    fposition += 1; // remember the equals sign
  }
#endif

    // ignore hidden keywords
    std::string s = i->first;
	if (s.find("hidden") != 0) 
	    *file << i->first << "=" << i->second << ";\n";
  }

  *file << "\f\n";
}

//----------------------------------------------------------------------------
// Writes a region in a file.  Subclasses can override this method
// to produce a header. This method only handles 3d data (plus components).
void vtkVFFWriter::WriteFile(ofstream *file, vtkImageData *data,
                               int extent[6], int wExtent[6])
{
  int idxY, idxZ;
  int rowLength; // in bytes
  void *ptr;
  unsigned long count = 0;
  unsigned long target;
  float progress = this->Progress;
  float area;
  char *write_buffer;
  int little = 0;

  // Make sure we actually have data.
//  if ( !data->GetPointData()->GetScalars())
//    {
//    vtkErrorMacro(<< "Could not get data from input.");
//    return;
//    }

  // determine little/big endian status
  short test_s = 10;
  vtkByteSwap::Swap2LE(&test_s);
  if (test_s == 10)
    little = 1;
  
  // take into consideration the scalar type
  switch (data->GetScalarType())
    {
    vtkTemplateMacro(
      rowLength = vtkImageWriterGetSize(static_cast<VTK_TT*>(0))
      );
    default:
      vtkErrorMacro(<< "Execute: Unknown output ScalarType");
      return;
    }
  rowLength *= data->GetNumberOfScalarComponents();
  rowLength *= (extent[1] - extent[0] + 1);

  // allocate space for a temporary buffer
  char *buffer = new char[rowLength];
  
  area = (float) ((extent[5] - extent[4] + 1)*
                  (extent[3] - extent[2] + 1)*
                  (extent[1] - extent[0] + 1)) /
         (float) ((wExtent[5] -wExtent[4] + 1)*
                  (wExtent[3] -wExtent[2] + 1)*
                  (wExtent[1] -wExtent[0] + 1));

  target = (unsigned long)((extent[5]-extent[4]+1)*
                           (extent[3]-extent[2]+1)/(50.0*area));
  target++;

  int ystart = extent[3];
  int yend = extent[2] - 1;
  int yinc = -1;
  if (this->FileLowerLeft)
    {
    ystart = extent[2];
    yend = extent[3]+1;
    yinc = 1;
    }
 
  int lower = extent[4];
  int upper = extent[5];
  
  for (idxZ = lower; idxZ <= upper; ++idxZ)
    {
    //this->GetInput()->UpdateInformation();
    //this->GetInput()->SetUpdateExtent(extent[0], extent[1], extent[2], extent[3], idxZ, idxZ);
    //this->GetInput()->Update();
	    
    for (idxY = ystart; idxY != yend; idxY = idxY + yinc)
      {
      if (!(count%target))
        {
        this->UpdateProgress(progress + count/(50.0*target));
        }
      count++;
      ptr = data->GetScalarPointer(extent[0], idxY, idxZ);

      if ((little == 1) && ((data->GetScalarType() == VTK_SHORT) ||
          (data->GetScalarType() == VTK_FLOAT))) {
	memcpy((char *)buffer, (char *) ptr, rowLength);
	vtkByteSwap::SwapVoidRange(buffer, rowLength, data->GetScalarSize());
	write_buffer = (char *)buffer;
      } else {
	write_buffer = (char *)ptr;
      }
#ifdef _REQUIRE_CHECKSUMS_
      EVP_DigestUpdate(&mdctx, write_buffer, rowLength);
#endif
      if ( ! file->write((char *)write_buffer, rowLength))
        {
        delete [] buffer;
        return;
        }
      }
    }
  delete [] buffer;
}


//----------------------------------------------------------------------------
const char * vtkVFFWriter::GetKeyword(const char *keyword)
{
  vtkstd::string s(keyword);
  static vtkstd::string t;
  t = this->header.header[s];
  return t.c_str();
}

//----------------------------------------------------------------------------
void vtkVFFWriter::SetKeyword(const char *keyword, const char *value)
{
  vtkstd::string s(keyword);
  vtkstd::string t(value);
  static const char * bad_keywords[] = {"size", "origin", "aspect", "format", "type",
	  		"bands", "bits", "spacing", "rank", "rawsize"};
  int i;
  // ignore certain strings
  for (i = 0; i < 10; i++)
  {
    if (s == bad_keywords[i])
      return;
  }
  
  this->header.header[s] = t;
}
