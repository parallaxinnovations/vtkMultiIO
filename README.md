Author: Jeremy Gill
Date: Nov 7, 2002

MultiIO package for VTK/python:

Here's a set of python classes for Kitware's VTK software, to hide the
details of getting both 2D and 3D image data, and geometry data into and
out of your code.  The classes wrap a number of different file format
handlers into a single set of 'super' classes. The classes use a
late-binding approach which is activated in the reader/writer's
SetFileName() method.

Supported image formats:
  
  Sun VFF images (single 2D, stack of 2D and 3D images; 8 bit byte, 16 bit ints and 32 bit floats (Intel only))
  MNI minc images (version 1 and 2)
  DICOM format images (2D, stack of 2D images reading; 3D image for writing)
  PNM (portable pixmap formats: pbm, pgm and pnm; 2D and stack of 2D)
  TIFF (tagged image file format) 2D and stack of 2D images (best support is for raw encoded images)
  VTK (2D and 3D images)
  SPR format - a simple raw file + header format
  NFO format - a simple raw file + header format (.nfo/.raw)
  PIL formats - An experimental wrapper that combines all the file formats supported by the python imaging
  library (http://www.pythonware.com/products/pil).  This includes jpeg, png, sgi, sun, eps and a whole lot more.
  Analyze format images - reader and writer for the popular MRI format
  Interfile file format
  HFH format images - Consists of a textual description file 'RECON.DAT', and a directory of images.

Supported geometry formats:

Supported file formats (for reading):
.VTK    -       VTK Polydata file
.obj    -       Wavefront OBJ file
.stl    -       Stereo lithography file
.bin    -       PLOT3D file
.oogl   -       Geomview OFF format file
.gts    -       GNU Triangulated Library file
.tec    -       Tecplot file
Supported file formats (for writing):
.VTK    -       VTK Polydata file
.iv     -       OpenInventor file
.stl    -       Stereo lithography file
.g      -       MOVIE.BYU file
.oogl   -       Geomview OFF format file
.gts    -       GNU Triangulated Library file

    
To use:

<snip>
  from vtkMultiIO import *

  # get a reader
  (reader,filters) = LoadImageReaders()
  
  # filename filter
  ft = []
  ft.append(("All files","*"))
  for i in range(len(filters)):
    ft.append((filters[i][1],'*'+filters[i][0]))
  
  # As the user for a filename
  filename = tkFileDialog.askopenfilename(filetypes=ft)
  
  # get the file
  reader.SetFileName(filename)
  reader.GetOutput()
  
</snip>

For 2D slices:
  Use the reader functions SetPrefix(), SetPattern() and SetDataExtent() as you would with the vtkPNMReader() class.

N.B.:

1. Because of the late-binding approach, it is critical that you call the SetFileName() member function
FIRST, before any other method of the reader or writer.

2. The PIL code is experimental.  At the moment it only has been attached to a vtkImageReader.  The filter list
   is not updated with PIL formats, because the sheer number of image formats becomes unweildly.  Basically, 
   try reading an image -- YMMV.

3. Use at your own risk.  There are known problems with the image orientation that still need to be hammered out.
   Other bugs certainly exist.

Thanks:

  David Gobbi contributed the original VFF and minc readers.
  Hua Qian contributed the original dicom reader and LIS L3d information.
  Paul Simedrea and Jaques Milner contributed the original GE reader.

  and Jeremy Gill wrote the wrapper functions, the SPR reader, the NFO reader and writer, the VFF writer,
  the Analyze reader/writer, the dicom writer and ported the L3D code from Hua, and massaged the rest of the 
  readers into shape.

Best of luck,

  Jeremy Gill <jgill@parallax-innovations.com>
