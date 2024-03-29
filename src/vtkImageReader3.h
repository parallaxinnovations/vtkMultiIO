#ifndef __vtkImageReader3_h
#define __vtkImageReader3_h

#include "vtkImageAlgorithm.h"

#if defined(__APPLE__)
#define COMMON_DIGEST_FOR_OPENSSL
#endif

//#define _REQUIRE_CHECKSUMS_
#ifdef _REQUIRE_CHECKSUMS_
#include <openssl/evp.h>
#endif

class vtkStringArray;

#define VTK_FILE_BYTE_ORDER_BIG_ENDIAN 0
#define VTK_FILE_BYTE_ORDER_LITTLE_ENDIAN 1

class VTK_EXPORT vtkImageReader3 : public vtkImageAlgorithm
{
public:
  static vtkImageReader3 *New();
  vtkTypeMacro(vtkImageReader3,vtkImageAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent) override;

  // Description:
  // Specify file name for the image file. If the data is stored in
  // multiple files, then use SetFileNames or SetFilePrefix instead.
  virtual void SetFileName(const char *);
  vtkGetStringMacro(FileName);

  // Description:
  // Specify a list of file names.  Each file must be a single slice,
  // and each slice must be of the same size. The files must be in the
  // correct order.
  // Use SetFileName when reading a volume (multiple slice), since
  // DataExtent will be modified after a SetFileNames call.
  virtual void SetFileNames(vtkStringArray *);
  vtkGetObjectMacro(FileNames, vtkStringArray);

  // Description:
  // Specify file prefix for the image file or files.  This can be
  // used in place of SetFileName or SetFileNames if the filenames
  // follow a specific naming pattern, but you must explicitly set
  // the DataExtent so that the reader will know what range of slices
  // to load.
  virtual void SetFilePrefix(const char *);
  vtkGetStringMacro(FilePrefix);

  char *GetMD5Sum(void);
  // Description:
  // The sprintf-style format string used to build filename from
  // FilePrefix and slice number.
  virtual void SetFilePattern(const char *);
  vtkGetStringMacro(FilePattern);

  void FinalizeDigest();

  // Description:
  // Set the data type of pixels in the file.
  // If you want the output scalar type to have a different value, set it
  // after this method is called.
  virtual void SetDataScalarType(int type);
  virtual void SetDataScalarTypeToFloat(){this->SetDataScalarType(VTK_FLOAT);}
  virtual void SetDataScalarTypeToDouble(){this->SetDataScalarType(VTK_DOUBLE);}
  virtual void SetDataScalarTypeToInt(){this->SetDataScalarType(VTK_INT);}
  virtual void SetDataScalarTypeToUnsignedInt(){this->SetDataScalarType(VTK_UNSIGNED_INT);}
  virtual void SetDataScalarTypeToShort(){this->SetDataScalarType(VTK_SHORT);}
  virtual void SetDataScalarTypeToUnsignedShort()
    {this->SetDataScalarType(VTK_UNSIGNED_SHORT);}
  virtual void SetDataScalarTypeToChar()
    {this->SetDataScalarType(VTK_CHAR);}
  virtual void SetDataScalarTypeToSignedChar()
    {this->SetDataScalarType(VTK_SIGNED_CHAR);}
  virtual void SetDataScalarTypeToUnsignedChar()
    {this->SetDataScalarType(VTK_UNSIGNED_CHAR);}

  void GetScalarRange(float range[2]);

  // Description:
  // Get the file format.  Pixels are this type in the file.
  vtkGetMacro(DataScalarType, int);

  // Description:
  // Set/Get the number of scalar components
  vtkSetMacro(NumberOfScalarComponents,int);
  vtkGetMacro(NumberOfScalarComponents,int);

  // Description:
  // Get/Set the extent of the data on disk.
  vtkSetVector6Macro(DataExtent,int);
  vtkGetVector6Macro(DataExtent,int);

  // Description:
  // The number of dimensions stored in a file. This defaults to two.
  vtkSetMacro(FileDimensionality, int);
  int GetFileDimensionality() {return this->FileDimensionality;}

  // Description:
  // Set/Get the spacing of the data in the file.
  vtkSetVector3Macro(DataSpacing,double);
  vtkGetVector3Macro(DataSpacing,double);

  // Description:
  // Set/Get the origin of the data (location of first pixel in the file).
  vtkSetVector3Macro(DataOrigin,double);
  vtkGetVector3Macro(DataOrigin,double);

  // Description:
  // Get the size of the header computed by this object.
  unsigned long GetHeaderSize();
  unsigned long GetHeaderSize(unsigned long slice);

  // Description:
  // If there is a tail on the file, you want to explicitly set the
  // header size.
  virtual void SetHeaderSize(unsigned long size);

  // Description:
  // These methods should be used instead of the SwapBytes methods.
  // They indicate the byte ordering of the file you are trying
  // to read in. These methods will then either swap or not swap
  // the bytes depending on the byte ordering of the machine it is
  // being run on. For example, reading in a BigEndian file on a
  // BigEndian machine will result in no swapping. Trying to read
  // the same file on a LittleEndian machine will result in swapping.
  // As a quick note most UNIX machines are BigEndian while PC's
  // and VAX tend to be LittleEndian. So if the file you are reading
  // in was generated on a VAX or PC, SetDataByteOrderToLittleEndian
  // otherwise SetDataByteOrderToBigEndian.
  virtual void SetDataByteOrderToBigEndian();
  virtual void SetDataByteOrderToLittleEndian();
  virtual int GetDataByteOrder();
  virtual void SetDataByteOrder(int);
  virtual const char *GetDataByteOrderAsString();

  // Description:
  // When reading files which start at an unusual index, this can be added
  // to the slice number when generating the file name (default = 0)
  vtkSetMacro(FileNameSliceOffset,int);
  vtkGetMacro(FileNameSliceOffset,int);

  // Description:
  // When reading files which have regular, but non contiguous slices
  // (eg filename.1,filename.3,filename.5)
  // a spacing can be specified to skip missing files (default = 1)
  vtkSetMacro(FileNameSliceSpacing,int);
  vtkGetMacro(FileNameSliceSpacing,int);


  // Description:
  // Set/Get the byte swapping to explicitly swap the bytes of a file.
  vtkSetMacro(SwapBytes,int);
  virtual int GetSwapBytes() {return this->SwapBytes;}
  vtkBooleanMacro(SwapBytes,int);

//BTX
  int GetFd() { return this->fd; }
  vtkGetVectorMacro(DataIncrements,unsigned long,4);
//ETX

  virtual int OpenFile();
  virtual void SeekFile(int i, int j, int k);

  // Description:
  // Set/Get whether the data comes from the file starting in the lower left
  // corner or upper left corner.
  vtkBooleanMacro(FileLowerLeft, int);
  vtkGetMacro(FileLowerLeft, int);
  vtkSetMacro(FileLowerLeft, int);

  // Description:
  // Set/Get the internal file name
  virtual void ComputeInternalFileName(int slice);
  vtkGetStringMacro(InternalFileName);

  // Description:
  // Return non zero if the reader can read the given file name.
  // Should be implemented by all sub-classes of vtkImageReader3.
  // For non zero return values the following values are to be used
  //   1 - I think I can read the file but I cannot prove it
  //   2 - I definitely can read the file
  //   3 - I can read the file and I have validated that I am the
  //       correct reader for this file
  virtual int CanReadFile(const char* vtkNotUsed(fname))
    {
      return 0;
    }

  // Description:
  // Get the file extensions for this format.
  // Returns a string with a space separated list of extensions in
  // the format .extension
  virtual const char* GetFileExtensions()
    {
      return 0;
    }

  // Description:
  // Return a descriptive name for the file format that might be useful in a GUI.
  virtual const char* GetDescriptiveName()
    {
      return 0;
    }
protected:
  vtkImageReader3();
  ~vtkImageReader3();

  vtkStringArray *FileNames;

  char *InternalFileName;
  char *FileName;
  char *FilePrefix;
  char *FilePattern;
  char *MD5Sum;
  int NumberOfScalarComponents;
  int FileLowerLeft;
  int Finalized;
  int fd;
  unsigned long DataIncrements[4];
  int DataExtent[6];
  int SwapBytes;

  int FileDimensionality;
  unsigned long HeaderSize;
  int DataScalarType;
  unsigned long ManualHeaderSize;

  double DataSpacing[3];
  double DataOrigin[3];

  int FileNameSliceOffset;
  int FileNameSliceSpacing;

  virtual int RequestInformation(vtkInformation* request,
                                 vtkInformationVector** inputVector,
                                 vtkInformationVector* outputVector);
  virtual void ExecuteInformation();

#if VTK_MAJOR_VERSION == 5
    virtual void ExecuteData(vtkDataObject *data);
#else
  virtual void ExecuteDataWithInformation(vtkDataObject *data, vtkInformation *outInfo);
#endif

  virtual void ComputeDataIncrements();
private:
  vtkImageReader3(const vtkImageReader3&);  // Not implemented.
  void operator=(const vtkImageReader3&);  // Not implemented.
#ifdef _REQUIRE_CHECKSUMS_
  EVP_MD_CTX mdctx;
  unsigned char md_value[EVP_MAX_MD_SIZE];
  const EVP_MD *md;
  unsigned int md_len;
#endif
};

#endif
