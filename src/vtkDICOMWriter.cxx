/* =========================================================================
*
* Copyright (c) 2000-2011 GE Healthcare
*
* Use, modification and redistribution of the software, in source or
* binary forms, are permitted provided that the following terms and
* conditions are met:
*
* 1) Redistribution of the source code, in verbatim or modified
*   form, must retain the above copyright notice, this license,
*   the following disclaimer, and any notices that refer to this
*   license and/or the following disclaimer.
*
* 2) Redistribution in binary form must include the above copyright
*    notice, a copy of this license and the following disclaimer
*   in the documentation or with other materials provided with the
*   distribution.
*
* 3) Modified copies of the source code must be clearly marked as such,
*   and must not be misrepresented as verbatim copies of the source code.
*
* EXCEPT WHEN OTHERWISE STATED IN WRITING BY THE COPYRIGHT HOLDERS AND/OR
* OTHER PARTIES, THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE
* SOFTWARE "AS IS" WITHOUT EXPRESSED OR IMPLIED WARRANTY INCLUDING, BUT
* NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
* FOR A PARTICULAR PURPOSE.  IN NO EVENT UNLESS AGREED TO IN WRITING WILL
* ANY COPYRIGHT HOLDER OR OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
* THE SOFTWARE UNDER THE TERMS OF THIS LICENSE BE LIABLE FOR ANY DIRECT,
* INDIRECT, INCIDENTAL OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
* TO, LOSS OF DATA OR DATA BECOMING INACCURATE OR LOSS OF PROFIT OR
* BUSINESS INTERRUPTION) ARISING IN ANY WAY OUT OF THE USE OR INABILITY TO
* USE THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
*
* ========================================================================= */

#include "vtkDICOMWriter.h"
#include "vtkImageData.h"
#include "vtkObjectFactory.h"
#include <medcon.h>

#undef min
#undef max
#define min(x,y) ((x) > (y)) ? (y) : (x)
#define max(x,y) ((x) < (y)) ? (y) : (x)

vtkCxxRevisionMacro(vtkDICOMWriter, "$Revision: 1.2 $");
vtkStandardNewMacro(vtkDICOMWriter);

vtkDICOMWriter::vtkDICOMWriter()
{
  this->FileLowerLeft = 1;
  this->FileDimensionality = 3;

   data = 0;
   pixelx = pixely = pixelz = 1.0;
   
   /* initialize FILEINFO struct */
   memset(&fi, 0, sizeof(fi));
   fi.ifp = fi.ofp = 0x0;
   fi.acqdata = NULL;
   strcpy(i_filename, "export.raw");
   strcpy(o_filename, "export.dcm");
   fi.map = MDC_MAP_GRAY;
   fi.format = MDC_FRMT_RAW;
   fi.rawconv = MDC_FRMT_RAW;
   fi.compression = 0;
   fi.truncated = 0;
   type = BIT8_U;
  
   fi.glmin = 0;
   fi.glmax = 255;
   fi.qglmin = 0;
   fi.qglmax = 255;
   
   fi.slice_projection = 0;
   fi.pat_slice_orient = 1;
   
   strcpy(fi.pat_pos, "Unknown");
   strcpy(fi.pat_orient, "Unknown");
   strcpy(fi.patient_sex, "Unknown");
   strcpy(fi.patient_name, "Unknown");
   strcpy(fi.patient_id, "Unknown");
   strcpy(fi.patient_dob, "Unknown");
   strcpy(fi.study_descr, "Unknown");
   strcpy(fi.study_name, "Unknown");
   
   fi.study_date_day = fi.study_date_month = fi.study_date_year = 0;
   fi.study_time_hour = fi.study_time_minute = fi.study_time_second = 0;  
}

void vtkDICOMWriter::SetDate(int year, int month, int day)
{
   fi.study_date_day = day;
   fi.study_date_month = month;
   fi.study_date_year = year;
}

void vtkDICOMWriter::SetTime(int hour, int minute, int second)
{
   fi.study_time_hour = hour;
   fi.study_time_minute = minute;
   fi.study_time_second = second;
}

vtkDICOMWriter::~vtkDICOMWriter()
{
}

//----------------------------------------------------------------------------
// Writes all the data from the input.
void vtkDICOMWriter::Write()
{
  // Set Progress to zero
  this->pvalue = 0.0;
   
  // Error checking
  if ( this->GetInput() == NULL )
    {
    vtkErrorMacro(<<"Write:Please specify an input!");
    return;
    }
  if (!this->FileName && !this->FilePrefix)
    {
    vtkErrorMacro(<<"Write:Please specify either a FileName or a file prefix and pattern");
    return;
    }
  
  // Make sure the file name is allocated
  this->InternalFileName = 
    new char[(this->FileName ? strlen(this->FileName) : 1) +
            (this->FilePrefix ? strlen(this->FilePrefix) : 1) +
            (this->FilePattern ? strlen(this->FilePattern) : 1) + 10];
  
  // Fill in image information.
  this->GetInput()->UpdateInformation();
  int *wExtent;
  wExtent = this->GetInput()->GetWholeExtent();
  this->FileNumber = this->GetInput()->GetWholeExtent()[4];
  this->UpdateProgress(0.0);
   
  // if dimensionality is 3, write file in one go
  if (this->FileName)
     {
	// generate internal file name
//        sprintf(this->InternalFileName, this->FilePattern,this->FileNumber);

	// snarf the whole image
	this->GetInput()->SetUpdateExtent(wExtent[0], wExtent[1],
					  wExtent[2], wExtent[3],
					  wExtent[4], wExtent[5]);
	
	// Update the input
	this->GetInput()->UpdateData();

	// Write the file
	this->WriteWholeImage(this->GetInput());
     }
   else // FileName isn't set -- dump a bunch of slices instead
     {
   
	// loop over the z axis and write the slices
	for (this->FileNumber = wExtent[4]; this->FileNumber <= wExtent[5]; 
	     ++this->FileNumber)
	  {
	     this->GetInput()->SetUpdateExtent(wExtent[0], wExtent[1],
					       wExtent[2], wExtent[3],
					       this->FileNumber, 
					       this->FileNumber);
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
	       }
	     this->GetInput()->UpdateData();
	     this->WriteSlice(this->GetInput());
	     this->UpdateProgress((this->FileNumber - wExtent[4])/
				  (wExtent[5] - wExtent[4] + 1.0));
	  }
     }
   
  delete [] this->InternalFileName;
  this->InternalFileName = NULL;
}

void vtkDICOMWriter::WriteWholeImage(vtkImageData *data)
{
  int px_min = 100000, px_max = -100000;
  char *cptr;
  unsigned short *sptr;
  float *fptr;
  void *outPtr;
  int* uext = data->GetUpdateExtent();
  int nx, ny, nz;
  
  // Call the correct templated function for the input
  outPtr = data->GetScalarPointer(uext[0], uext[2], uext[4]);
      
  if ((data->GetScalarType() < VTK_CHAR) || (data->GetScalarType() > VTK_UNSIGNED_SHORT))
    {
    vtkWarningMacro("DICOMWriter only supports char and short input");
    return;
    }   

  if (data->GetNumberOfScalarComponents() > 1)
    {
    vtkErrorMacro("Exceed DICOM limits for number of components (" << data->GetNumberOfScalarComponents() << " > " << 1 << ")" );
    return;
    }

   nz = uext[5]-uext[4]+1;
   nx = uext[1]-uext[0]+1;
   ny = uext[3]-uext[2]+1;
   fi.number = nz;
   fi.mwidth = nx;
   fi.mheight = ny;

/* determine depth, data type */
   switch (data->GetScalarType()) 
     {
      case 2:
	type = BIT8_S; depth = 8; break;
      case 3:
	type = BIT8_U; depth = 8; break;
      case 4:
	type = BIT16_S; depth = 16; break;
      case 5:
	type = BIT16_U; depth = 16; break;
      case 6:
	type = BIT16_S; depth = 16; break;
      case 7:
	type = BIT16_U;	depth = 16; break;
      case 8:
	type = BIT32_S; depth = 32; break;
      case 9:
	type = BIT32_U;	depth = 32; break;
      case 10:
	type = FLT32; depth = 32; break;
     }
  
   fi.bits = depth;

   strcpy(i_filename, this->FileName);  
   fi.ifname = (char *) i_filename;
   fi.ofname = (char *) o_filename;
   
   fi.dim[0] = 4;
   fi.dim[1] = nx;
   fi.dim[2] = ny;
   fi.dim[3] = nz;
   fi.dim[4] = 1;
   fi.dim[5] = 1;
   fi.dim[6] = 1;
   fi.dim[7] = 1;
   fi.pixdim[0] = 3;

   float *sp = data->GetSpacing();   
   fi.pixdim[1] = sp[0];
   fi.pixdim[2] = sp[1];
   fi.pixdim[3] = sp[2];
   fi.pixdim[4] = 1;
   fi.pixdim[5] = 1;
   fi.pixdim[6] = 1;
   fi.pixdim[7] = 1;
   
   /* this should be replaced */
   fi.endian = MDC_HOST_ENDIAN;
     
   /* allocate image */
   fi.image = (IMG_DATA *) malloc(sizeof(IMG_DATA) * nz);

   long i, j;
   for (i = 0; i < nz; i++)
     {
    this->UpdateProgress((float) i / (float) nz);
	fi.image[i].buf = (Uint8 *) outPtr + (i * nx * ny * (depth / 8));
	fi.image[i].width = nx;
	fi.image[i].height = ny;
	fi.image[i].bits = depth;
	fi.image[i].type = type;
	fi.image[i].flags = 0;	

	/* determine image min/max */
	switch (depth) 
	  {
	     case 8:
	     cptr =  (char *) fi.image[i].buf;
	     for (j = 0; j < (nx*ny); j++)
	       {
		  px_min = min(px_min, *cptr);
		  px_max = max(px_max, *cptr++);
	       }
	     break;
	     case 16:
	     sptr = (unsigned short *) fi.image[i].buf;
	     for (j = 0; j < (nx*ny); j++)
	       {
		  px_min = min(px_min, *sptr);
		  px_max = max(px_max, *sptr++);
	       }
	     break;
	     case 32:
	     fptr = (float *) fi.image[i].buf;
	     for (j = 0; j < (nx*ny); j++)
	       {
		  px_min = min(px_min, *fptr);
		  px_max = max(px_max, *fptr++);
	       }
	     break;
	  }
		
	fi.image[i].min = px_min;
	fi.image[i].max = px_max;
	fi.image[i].qmin = px_min;
	fi.image[i].qmax = px_max;
	fi.image[i].fmin = px_min;
	fi.image[i].fmax = px_max;
	fi.image[i].qfmin = px_min;
	fi.image[i].qfmax = px_max;
	fi.image[i].rescale_slope = 1;
	fi.image[i].rescale_intercept = 0;
	fi.image[i].quant_units = 1;
	fi.image[i].calibr_units = 1;
	fi.image[i].quant_scale = 1;
	fi.image[i].calibr_fctr = 1;
	fi.image[i].pixel_xsize = sp[0];
	fi.image[i].pixel_ysize = sp[1];
	fi.image[i].slice_width = sp[2];
	fi.image[i].frame_start = 0;
	fi.image[i].frame_duration = 0;
	fi.image[i].recon_scale = 0;
	fi.image[i].image_pos_dev[0] = 0;
	fi.image[i].image_pos_dev[1] = 0;
	fi.image[i].image_pos_dev[2] = 0;
	fi.image[i].image_pos_pat[0] = -(nx * sp[0] / 2.0);
	fi.image[i].image_pos_pat[1] = -(ny * sp[1] / 2.0);
	fi.image[i].image_pos_pat[2] = (uext[4] -(nz/2.0)) * sp[2];
     }

   MDC_NO_PREFIX = MDC_YES;
   MdcPrefix(0);
   MdcWriteDICM(&fi);
   this->UpdateProgress(1.0);
   
   free(fi.image);
}

void vtkDICOMWriter::WriteSlice(vtkImageData *data)
{
  // Call the correct templated function for the output
  void *outPtr;
  int* uext = data->GetUpdateExtent();
  int px_min = 100000, px_max = -100000;
  char *cptr;
  unsigned short *sptr;
  float *fptr;
  int nx, ny, nz;

   
  // Call the correct templated function for the input
  outPtr = data->GetScalarPointer(uext[0], uext[2], uext[4]);
//  if (data->GetScalarType() != VTK_UNSIGNED_CHAR)
//    {
//    vtkWarningMacro("DICOMWriter only supports unsigned char input");
//    return;
//    }   

  if (data->GetNumberOfScalarComponents() > 1)
    {
    vtkErrorMacro("Exceed DICOM limits for number of components (" << data->GetNumberOfScalarComponents() << " > " << 1 << ")" );
    return;
    }
  
  // set the destination file

  // The code that follows was ripped out from WriteWholeImage()  
  // Call the correct templated function for the input
  outPtr = data->GetScalarPointer(uext[0], uext[2], uext[4]);
      
  if ((data->GetScalarType() < VTK_CHAR) || (data->GetScalarType() > VTK_UNSIGNED_SHORT))
    {
    vtkWarningMacro("DICOMWriter only supports char and short input");
    return;
    }   

  if (data->GetNumberOfScalarComponents() > 1)
    {
    vtkErrorMacro("Exceed DICOM limits for number of components (" << data->GetNumberOfScalarComponents() << " > " << 1 << ")" );
    return;
    }

   nx = uext[1]-uext[0]+1;
   ny = uext[3]-uext[2]+1;
   nz = 1;
   fi.number = nz;
   fi.mwidth = nx;
   fi.mheight = ny;

/* determine depth, data type */
   switch (data->GetScalarType()) 
     {
      case 2:
	type = BIT8_S; depth = 8; break;
      case 3:
	type = BIT8_U; depth = 8; break;
      case 4:
	type = BIT16_S; depth = 16; break;
      case 5:
	type = BIT16_U; depth = 16; break;
      case 6:
	type = BIT16_S; depth = 16; break;
      case 7:
	type = BIT16_U;	depth = 16; break;
      case 8:
	type = BIT32_S; depth = 32; break;
      case 9:
	type = BIT32_U;	depth = 32; break;
      case 10:
	type = FLT32; depth = 32; break;
     }
  
   fi.bits = depth;

   strcpy(i_filename, this->InternalFileName);  
   fi.ifname = (char *) i_filename;
   fi.ofname = (char *) o_filename;
   
   fi.dim[0] = 4;
   fi.dim[1] = nx;
   fi.dim[2] = ny;
   fi.dim[3] = nz;
   fi.dim[4] = 1;
   fi.dim[5] = 1;
   fi.dim[6] = 1;
   fi.dim[7] = 1;
   fi.pixdim[0] = 3;

   float *sp = data->GetSpacing();   
   fi.pixdim[1] = sp[0];
   fi.pixdim[2] = sp[1];
   fi.pixdim[3] = sp[2];
   fi.pixdim[4] = 1;
   fi.pixdim[5] = 1;
   fi.pixdim[6] = 1;
   fi.pixdim[7] = 1;
   
   /* this should be replaced */
   fi.endian = MDC_HOST_ENDIAN;
     
   /* allocate image */
   fi.image = (IMG_DATA *) malloc(sizeof(IMG_DATA) * nz);

   long i, j, k;
   for (i = 0; i < nz; i++)
     {
	fi.image[i].buf = (Uint8 *) outPtr + (i * nx * ny * (depth / 8));
	fi.image[i].width = nx;
	fi.image[i].height = ny;
	fi.image[i].bits = depth;
	fi.image[i].type = type;
	fi.image[i].flags = 0;	

	/* determine image min/max */
	switch (depth) 
	  {
	     case 8:
	     cptr =  (char *) fi.image[i].buf;
	     for (j = 0; j < (nx*ny); j++)
	       {
		  px_min = min(px_min, *cptr);
		  px_max = max(px_max, *cptr++);
	       }
	     break;
	     case 16:
	     sptr = (unsigned short *) fi.image[i].buf;
	     for (j = 0; j < (nx*ny); j++)
	       {
		  px_min = min(px_min, *sptr);
		  px_max = max(px_max, *sptr++);
	       }
	     break;
	     case 32:
	     fptr = (float *) fi.image[i].buf;
	     for (j = 0; j < (nx*ny); j++)
	       {
		  px_min = min(px_min, *fptr);
		  px_max = max(px_max, *fptr++);
	       }
	     break;
	  }
		
	fi.image[i].min = px_min;
	fi.image[i].max = px_max;
	fi.image[i].qmin = px_min;
	fi.image[i].qmax = px_max;
	fi.image[i].fmin = px_min;
	fi.image[i].fmax = px_max;
	fi.image[i].qfmin = px_min;
	fi.image[i].qfmax = px_max;
	fi.image[i].rescale_slope = 1;
	fi.image[i].rescale_intercept = 0;
	fi.image[i].quant_units = 1;
	fi.image[i].calibr_units = 1;
	fi.image[i].quant_scale = 1;
	fi.image[i].calibr_fctr = 1;
	fi.image[i].pixel_xsize = sp[0];
	fi.image[i].pixel_ysize = sp[1];
	fi.image[i].slice_width = sp[2];
	fi.image[i].frame_start = 0;
	fi.image[i].frame_duration = 0;
	fi.image[i].recon_scale = 0;
 	fi.image[i].image_pos_dev[0] = 0;
	fi.image[i].image_pos_dev[1] = 0;
	fi.image[i].image_pos_dev[2] = 0;
  	fi.image[i].image_pos_pat[0] = -(nx * sp[0] / 2.0);
	fi.image[i].image_pos_pat[1] = -(ny * sp[1] / 2.0);
	fi.image[i].image_pos_pat[2] = (uext[4] -(nz/2.0))* sp[2];
     }
   MDC_NO_PREFIX = MDC_YES;
   MdcPrefix(0);
   MdcWriteDICM(&fi);
   
   free(fi.image);
}

void vtkDICOMWriter::PrintSelf(ostream& os, vtkIndent indent)
{
  this->Superclass::PrintSelf(os,indent);

  os << indent << "Patient ID: " << 0 << "\n";
  os << indent << "Patient Name: " << 0 << "\n";
  os << indent << "Scan Date: " << 0 << "\n";
  os << indent << "Scan Time: " << 0 << "\n";
}
