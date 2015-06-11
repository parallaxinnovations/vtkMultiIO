// .NAME vtkVFFReader - a vff image reader
// .SECTION Description
// .SECTION See Also
// vtkJPEGReader vtkPNGReader vtkImageReader vtkGESignaReader

#ifndef __vtkVFFReader_h
#define __vtkVFFImageReader_h
#include "vtkImageReader3.h"
#include "vtkMultiIOConfigure.h"
#include "vtkVFFHeaderInternal.h"

class vtkVFFHeaderInternal;

class VTK_vtkMultiIO_EXPORT vtkVFFReader : public vtkImageReader3
{
public:
  static vtkVFFReader *New();
  vtkTypeRevisionMacro(vtkVFFReader, vtkImageReader3);
  void PrintSelf(ostream& os, vtkIndent indent);   

  // Description:
  // Set/Get whether the data comes from the file starting in the lower left
  // corner or upper left corner.
  vtkGetMacro(Water, double);
  vtkSetMacro(Water, double);
  vtkGetMacro(Air, double);
  vtkSetMacro(Air, double);
  vtkGetMacro(boneHU, long);
  vtkSetMacro(boneHU, long);
  vtkSetStringMacro(Title);
  vtkGetStringMacro(Title);
  vtkSetStringMacro(Subject);
  vtkGetStringMacro(Subject);
  vtkSetStringMacro(Date);
  vtkGetStringMacro(Date);

  int CanReadFile(const char* fname);
  void ExecuteInformation();
  int GetNumberOfKeywords();
  const char *GetKeyword(const char *key);
  const char *GetKeywordNameByNumber(const int index);
  void SetKeyword(const char *key, const char *value);
  
protected:
  vtkVFFReader();
  ~vtkVFFReader();
  double Water;
  double Air;
  long boneHU;
  char *Title;
  char *Subject;
  char *Date;
  vtkVFFHeaderInternal header;
  
private:
  vtkVFFReader(const vtkVFFReader&);  // Not implemented.
  void operator=(const vtkVFFReader&);  // Not implemented.
};

#endif
