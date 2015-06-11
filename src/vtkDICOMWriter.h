// .NAME vtkDICOMWriter - Writes DICOM files.
// .SECTION Description
// vtkDICOMWriter writes DICOM files.
//
// .SECTION See Also
// vtkDICOMReader

#ifndef __vtkDICOMWriter_h
#define __vtkDICOMWriter_h

#include "vtkImageWriter.h"
#include "vtkMultiIOConfigure.h"

#ifdef __cplusplus
extern "C" {
#endif
#include <medcon.h>
#ifdef __cplusplus
}
#endif

class vtkUnsignedCharArray;
class vtkImageData;

class VTK_vtkMultiIO_EXPORT vtkDICOMWriter : public vtkImageWriter
{
public:
  static vtkDICOMWriter *New();
  vtkTypeRevisionMacro(vtkDICOMWriter,vtkImageWriter);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // The main interface which triggers the writer to start.
  virtual void Write();
   
  void SetDate(int year, int month, int day);
  void SetTime(int hour, int minute, int second); 
   
protected:
  vtkDICOMWriter();
  ~vtkDICOMWriter();
  
  void WriteSlice(vtkImageData *data);
  void WriteWholeImage(vtkImageData *data);   
   
private:
  FILEINFO fi;
  unsigned char *data;
  char i_filename[80];
  char o_filename[80];
  int nx;
  int ny;
  int nz;
  int depth;
  int type;
  int endian;
  float pixelx;
  float pixely;
  float pixelz;  
  float pvalue;
  vtkDICOMWriter(const vtkDICOMWriter&);  // Not implemented.
  void operator=(const vtkDICOMWriter&);  // Not implemented.
  char *MdcWriteDICM(FILEINFO *fi);
  char *MdcDicomWriteG7FE0(FILEINFO *fi, MDC_DICOM_STUFF_T *dicom);
};

#endif


