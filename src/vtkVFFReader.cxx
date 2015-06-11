#include "vtkVFFReader.h"
#include "vtkConfigure.h"
#include "vtkObjectFactory.h"

vtkCxxRevisionMacro(vtkVFFReader, "$Revision: 1.2 $");
vtkStandardNewMacro(vtkVFFReader);


//----------------------------------------------------------------------------
void vtkVFFReader::ExecuteInformation()
{
  FILE *fp;
  char line[1024];
  int pos0, pos1, dims;
  float ftemp;
  long ltemp;
    
  this->ComputeInternalFileName(this->DataExtent[4]);
  if (this->InternalFileName == NULL || this->InternalFileName[0] == '\0')
    return;

  fp = fopen(this->InternalFileName, "rb");

  // parse first line -- should be 'ncaa'
  fgets(line, 1024, fp);
  if (strncmp(line, "ncaa", 4)) {
    vtkErrorMacro(<< "Invalid header.  First line must read 'ncaa'");
    vtkErrorMacro(<< "offending line: '" << line << "'");
    fclose(fp);
    return;
  }
  
  fgets(line, 1024, fp); 
  while (line[0] != '\f') {
    pos1 = strlen(line);
    
    // cleanup the end of the line (find ';')
    while ((pos1) && (line[pos1] != ';'))
      pos1--;
    if (line[pos1] != ';') {
      vtkErrorMacro(<< "Header line must end with ';'");
      fclose(fp);
      return;
    }
    line[pos1] = '\0';
    
    // cleanup (find last non-whitespace)
    while ((pos1) && ((line[pos1-1] == ' ') || (line[pos1-1] == '\t')))
      line[--pos1] = '\0';
   
    // now separate key from value 
    for (pos0=0; (pos0 <= pos1) && (line[pos0] != '='); pos0++);
    if (pos0 >= pos1) {
      vtkErrorMacro(<<"Invalid header line. Offending contents: " << line);
      fclose(fp);
      return;
    }
    line[pos0] = '\0';
   
    // add key/value pair to header structure
    this->header.header[vtkstd::string(line)] = vtkstd::string(&line[pos0+1]);

    // read next line
    fgets(line, 1024, fp);
  }

  // throw away some stuff
  this->header.header.erase(vtkstd::string("format"));
  this->header.header.erase(vtkstd::string("type"));
  
  // parse air
  vtkstd::string t = this->header.header[vtkstd::string("air")];
  if (sscanf(t.c_str(), "%f", &ftemp) == 1) {
    this->SetAir(ftemp);
    this->header.header.erase(vtkstd::string("air"));
  }

  // parse water
  t = this->header.header[vtkstd::string("water")];
  if (sscanf(t.c_str(), "%f", &ftemp) == 1) {
    this->SetWater(ftemp);
    this->header.header.erase(vtkstd::string("water"));
  }

  // parse boneHU
  t = this->header.header[vtkstd::string("boneHU")];
  if (sscanf(t.c_str(), "%ld", &ltemp) == 1) {
    this->SetboneHU(ltemp);
    this->header.header.erase(vtkstd::string("boneHU"));
  }

  // parse title
  t = this->header.header[vtkstd::string("title")];
  if (strlen(t.c_str())) {
    this->SetTitle(t.c_str());
    this->header.header.erase(vtkstd::string("title"));
  }
  
  // parse subject
  t = this->header.header[vtkstd::string("subject")];
  if (strlen(t.c_str())) {
    this->SetSubject(t.c_str());
    this->header.header.erase(vtkstd::string("subject"));
  }  

  // parse 'bands' field
  t = this->header.header[vtkstd::string("bands")];
  if (sscanf(t.c_str(), "%ld", &ltemp) == 1) {
    this->SetNumberOfScalarComponents(ltemp);
    this->header.header.erase(vtkstd::string("bands"));
  }
  
  // parse 'bits' field
  t = this->header.header[vtkstd::string("bits")];
  if (sscanf(t.c_str(), "%ld", &ltemp) == 1) {
    switch (ltemp) {
        case 8:
            this->SetDataScalarTypeToUnsignedChar();
            break;
        case 16:
            this->SetDataScalarTypeToShort();
            break;
        case 32:
            this->SetDataScalarTypeToFloat();
            break;
        default:
            vtkErrorMacro(<< "unknown bit depth. aborting.");
            fclose(fp);
            return;
    }
    this->header.header.erase(vtkstd::string("bits"));
  } else {
    vtkErrorMacro(<< "cannot parse 'bits' line.  aborting.");
    fclose(fp);
    return;
  }
 
  // parse 'dimensionality' field
  t = this->header.header[vtkstd::string("rank")];
  if (sscanf(t.c_str(), "%ld", &ltemp) == 1) {
    dims = ltemp;
    this->SetFileDimensionality(ltemp);
    this->header.header.erase(vtkstd::string("rank"));
  } else {
      vtkErrorMacro(<< "cannot parse 'rank' line. aborting.");
      return;
  }
 
  // parse 'size' field
  int sx = 1, sy = 1, sz = 1;
  t = this->header.header[vtkstd::string("size")];
  if (sscanf(t.c_str(), "%d %d %d", &sx, &sy, &sz) >= dims) {
    this->SetDataExtent(0, sx-1, 0, sy-1, 0, sz-1);
    this->header.header.erase(vtkstd::string("size"));
  } else {
    vtkErrorMacro(<< "cannot parse 'dims' line. aborting.");
    fclose(fp);
    return;
  }
 
  // parse 'spacing' field
  double spx = 1.0, spy = 1.0, spz = 1.0;
  t = this->header.header[vtkstd::string("spacing")];
  if (sscanf(t.c_str(), "%lf %lf %lf", &spx, &spy, &spz) >= dims) {
    this->header.header.erase(vtkstd::string("spacing"));
  } else {
    vtkErrorMacro(<< "cannot parse 'spacing' line. aborting.");
    fclose(fp);
    return;
  }

  // multiply by 'elementsize' field
  t = this->header.header[vtkstd::string("elementsize")];
  if (sscanf(t.c_str(), "%f", &ftemp) == 1) {
    spx *= ftemp; spy *= ftemp; spz *= ftemp;
    // import - delete element size here!!
    this->header.header.erase(vtkstd::string("elementsize"));
  }

  this->SetDataSpacing(spx, spy, spz);
 
  // parse 'origin' field
  float ox = 0.0, oy = 0.0, oz = 0.0;
  t = this->header.header[vtkstd::string("origin")];
  if (sscanf(t.c_str(), "%f %f %f", &ox, &oy, &oz) >= dims) {
    std::cout << ox << "," << oy << "," << oz << "\n";
    ox *= spx; oy *= spy; oz *= spz;
    this->SetDataOrigin(ox, oy, oz);
    this->header.header.erase(vtkstd::string("origin"));
  }  
  fclose(fp);
}

//----------------------------------------------------------------------------
int vtkVFFReader::CanReadFile(const char* fname)
{
  // get the magic number by reading in a file
  FILE* fp = fopen(fname,"rb");
  if (!fp)
    {
    return 0;
    }

  // compare magic number to determine file type
  if ((fgetc(fp) != 'n')||(fgetc(fp) != 'c')||(fgetc(fp) != 'a')||
        (fgetc(fp) != 'a') )
    {
    fclose(fp);
    return 0;
    }

  fclose(fp);
  return 1;
}

//----------------------------------------------------------------------------
int vtkVFFReader::GetNumberOfKeywords()
{
  return this->header.header.size();
}

//----------------------------------------------------------------------------
const char *vtkVFFReader::GetKeywordNameByNumber(const int index)
{
  vtkstd::map<vtkStdString, vtkStdString>::iterator it;
  static vtkstd::string t;

  if (index >= (int)this->header.header.size())
    return 0;
  
  it = this->header.header.begin();
  
  for (int i = 0; i < index; i++)
    it++;

  t = it->first;
  return t.c_str();
}


//----------------------------------------------------------------------------
const char * vtkVFFReader::GetKeyword(const char *keyword)
{
    vtkstd::string s(keyword);
    static vtkstd::string t;
    t = this->header.header[s];
    return t.c_str();
}

//----------------------------------------------------------------------------
void vtkVFFReader::SetKeyword(const char *keyword, const char *value)
{
    vtkstd::string s(keyword);
    vtkstd::string t(value);
    this->header.header[s] = t;
}


//----------------------------------------------------------------------------
vtkVFFReader::vtkVFFReader()
{
    this->Water = 0.0;
    this->Air = 0.0;
    this->boneHU = 0;
    this->Title = 0;
    this->Date = 0;
    this->Subject = 0;
    this->header.header.clear();
}

//----------------------------------------------------------------------------
vtkVFFReader::~vtkVFFReader()
{
    this->SetTitle(0);
    this->SetDate(0);
    this->SetSubject(0);
}

//----------------------------------------------------------------------------
void vtkVFFReader::PrintSelf(ostream& os, vtkIndent indent)
{
    this->Superclass::PrintSelf(os,indent);

    os << indent << "Title: " << (this->Title ? this->Title : "unknown") << "\n";
    os << indent << "Subject: " << (this->Subject ? this->Subject : "unknown") << "\n";
    os << indent << "Date: " << (this->Date ? this->Date : "unknown") << "\n";
    os << indent << "Air: " << (this->Air) << "\n";
    os << indent << "Water: " << (this->Water) << "\n";
    os << indent << "boneHU: " << (this->boneHU) << "\n";

    // okay, we've extracted all the header info -- now convert map values into vtk variables
    vtkstd::map<vtkStdString, vtkStdString>::iterator curr;
    curr = this->header.header.begin(); 
    os << indent << "Unparsed header key/values:\n";  
    for (vtkstd::map<vtkStdString, vtkStdString>::iterator i = this->header.header.begin();
       i != this->header.header.end(); ++i)
    os << indent << indent << i->first << ": " << i->second << "\n";
}
