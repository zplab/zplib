import numpy
import celiagg
from _gouraud_triangles import lib as _gouraud
from _gouraud_triangles import ffi as _ffi

def _cast(ptype, array):
    return _ffi.cast(ptype, array.ctypes.data)

def draw_mask(image_shape, geometry, antialias=False):
    """Draw a mask (0-255) from a given celiagg path.

    Note: to produce a True/False mask from the output, simply do the following:
        mask = draw_mask(image_shape, geometry)
        bool_mask = mask > 0

    Parameters:
        image_shape: shape of the resulting image
        geometry: celiagg VertexSource class, such as celiagg.Path or
            celiagg.BSpline, containing geometry to draw
        antialias: if False (default), output contains only 0 and 255. If True,
            output will be antialiased (better for visualization).

    Returns: mask array of dtype numpy.uint8
    """
    image = numpy.zeros(image_shape, dtype=numpy.uint8, order='F')
    # NB celiagg uses (h, w) C-order convention for image shapes, so give it the transpose
    canvas = celiagg.CanvasG8(image.T)
    state = celiagg.GraphicsState(drawing_mode=celiagg.DrawingMode.DrawFill, anti_aliased=antialias)
    fill = celiagg.SolidPaint(1,1,1)
    transform = celiagg.Transform()
    canvas.draw_shape(geometry, transform, state, fill=fill)
    return image

def gouraud_triangle_strip(triangle_strip, vertex_vals, shape, accumulate=False):
    """Return a triangle strip Gouraud-shaded based on values at each vertex.

    Parameters:
        triangle_strip: shape (n, 2) array of vertices describing a strip of
            connected triangles (such that vertices (0,1,2) describe the first
            triangle, vertices (1,2,3) describe the second, and so forth).
        vertex_vals: shape (n,) or (n, m) array of values associated with each
            vertex. In case of shape (n, m) this indicates m distinct sets of
            values for each vertex; as such m distinct output images will be
            produced.
        shape: shape of the output image(s).
        accumulate: if True, output values will be added atop one another in
            in cases where triangles overlap. (Useful for finding such cases.)

    Returns: single image (if vertex_vals is 1-dim) or list of images (if
        vertex_vals is > 1-dim), where each image contains the interpolation
        of the values at each vertex.
    """
    triangle_strip = numpy.asarray(triangle_strip, dtype=numpy.float32, order='C')
    vertex_vals = numpy.asarray(vertex_vals, dtype=numpy.float32, order='C')
    assert triangle_strip.ndim == 2 and triangle_strip.shape[1] == 2 and len(triangle_strip) > 2
    assert vertex_vals.ndim in (1, 2)
    unpack_out = False
    if vertex_vals.ndim == 1:
        vertex_vals = vertex_vals[:, numpy.newaxis]
        unpack_out = True
    assert len(vertex_vals) == len(triangle_strip)
    num_vertices = len(triangle_strip)
    out = numpy.zeros(tuple(shape)+vertex_vals.shape[1:], dtype=numpy.float32, order='F')
    _gouraud.gouraud_triangle_strip(num_vertices,
        _cast('float *', triangle_strip),
        _cast('float *', vertex_vals),
        _cast('float *', out),
        out.shape, out.strides, accumulate)
    if unpack_out:
        return out[:,:,0]
    else:
        return out.transpose((2,0,1))

def mask_triangle_strip(triangle_strip, shape):
    """Return a triangle strip rasterized into a boolean mask.

    Mask is guaranteed to be identical to the region drawn by gouraud_triangle_strip,
    which is not necessarily exactly the case for draw_mask() (which uses a
    slightly different algorithm internally).

    Parameters:
        triangle_strip: shape (n, 2) array of vertices describing a strip of
            connected triangles (such that vertices (0,1,2) describe the first
            triangle, vertices (1,2,3) describe the second, and so forth).
        shape: shape of the output image(s).

    Returns: bool image of specified shape.
    """
    triangle_strip = numpy.asarray(triangle_strip, dtype=numpy.float32, order='C')
    assert triangle_strip.ndim == 2 and triangle_strip.shape[1] == 2 and len(triangle_strip) > 2
    num_vertices = len(triangle_strip)
    out = numpy.zeros(tuple(shape), dtype=bool, order='F')
    _gouraud.mask_triangle_strip(num_vertices,
        _cast('float *', triangle_strip),
        _cast('float *', out),
        out.shape, out.strides)
    return out
