#include "vtkMultiIOEventObject.h"
#include "vtkObjectFactory.h"

vtkCxxRevisionMacro(vtkMultiIOEventObject, "$Revision: 1.2 $");
vtkStandardNewMacro(vtkMultiIOEventObject);

vtkMultiIOEventObject::vtkMultiIOEventObject()
{
	this->UserEventText = NULL;
}

void vtkMultiIOEventObject::Execute()
{
  vtkDebugMacro(<<"vtkMultiIOEventObject::Execute() called");
}

void vtkMultiIOEventObject::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);
  os << indent << "blah blah" << "\n";
}

