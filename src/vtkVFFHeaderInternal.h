#ifndef __vtkVFFHeaderInternal_h
#define __vtkVFFHeaderInternal_h

#include <map>
#include "vtkMultiIOConfigure.h"

#include "vtkStdString.h"

class vtkVFFHeaderInternal
{
public:
  typedef std::map<vtkStdString, vtkStdString> VFFHeaderMap;

  VFFHeaderMap header;
};


#endif
