#ifndef __vtkVFFWriter_h
#define __vtkVFFWriter_h

#include "vtkImageWriter.h"
#include "vtkMultiIOConfigure.h"
#include "vtkVFFHeaderInternal.h"

class vtkVFFHeaderInternal;

//#define _REQUIRE_CHECKSUMS_

#ifdef _REQUIRE_CHECKSUMS_
#define DIGEST_TYPE "md5"
#include <openssl/evp.h>
#endif

class VTK_vtkMultiIO_EXPORT vtkVFFWriter : public vtkImageWriter
{
public:
  static vtkVFFWriter *New();
  vtkTypeRevisionMacro(vtkVFFWriter,vtkImageWriter);
  void PrintSelf(ostream& os, vtkIndent indent);
  const char *GetKeyword(const char *key);
  void SetKeyword(const char *key, const char *value);
  void SetTitle(const char *value) { this->SetKeyword("title", value); }
  //virtual void RecursiveWrite(int dim, vtkImageData *region, ofstream *file);
  virtual void RecursiveWrite(int axis, vtkImageData *cache, vtkInformation* inInfo, ofstream *file);
  virtual void RecursiveWrite(int axis, vtkImageData *cache, vtkImageData *data, vtkInformation* inInfo, ofstream *file);

protected:
  vtkVFFWriter();
  ~vtkVFFWriter();
  vtkVFFHeaderInternal header;

  virtual void WriteFile(ofstream *file, vtkImageData *data, 
                         int extent[6], int wExtent[6]);
  virtual void WriteFileHeader(ofstream *, vtkImageData *, int [6]);
private:
  vtkVFFWriter(const vtkVFFWriter&);  // Not implemented.
  void operator=(const vtkVFFWriter&);  // Not implemented.
  long fposition; // file location where md5sum hexdigest should be written to

#ifdef _REQUIRE_CHECKSUMS_
  EVP_MD_CTX mdctx;
  unsigned char md_value[EVP_MAX_MD_SIZE];
  const EVP_MD *md;
  unsigned int md_len;
#endif

};

#endif


