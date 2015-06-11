#ifndef __vtkMultiIOEventObject_h
#define __vtkMultiIOEventObject_h

#include "vtkObject.h"
#include "vtkMultiIOConfigure.h"

class VTK_vtkMultiIO_EXPORT vtkMultiIOEventObject : public vtkObject 
{
public:
  static vtkMultiIOEventObject *New();
  vtkTypeRevisionMacro(vtkMultiIOEventObject,vtkObject);
  void PrintSelf(ostream& os, vtkIndent indent);

  // Description:
  // Set the current user-defined event type -- fill in this string to give
  // VTK's user-defined event more meaning
  vtkSetStringMacro(UserEventText);
  vtkGetStringMacro(UserEventText);
  
protected:
  vtkMultiIOEventObject();
  ~vtkMultiIOEventObject() { delete [] this->UserEventText; this->UserEventText = NULL; }
  char *UserEventText;

  void Execute();
private:
  vtkMultiIOEventObject(const vtkMultiIOEventObject&);  // Not implemented.
  void operator=(const vtkMultiIOEventObject&);  // Not implemented.
};

#endif


