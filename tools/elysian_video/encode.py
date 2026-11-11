"""Encode Skia frames in process; avoids piping uncompressed 1440p through Windows."""
from fractions import Fraction
import os

import av
import numpy as np
import skia

from .__main__ import WIDTH, HEIGHT, FPS


def encode_scene(target, count, draw, preset='medium', threads=3):
    pixels=np.empty((HEIGHT,WIDTH,4),dtype=np.uint8)
    info=skia.ImageInfo.Make(WIDTH,HEIGHT,skia.ColorType.kBGRA_8888_ColorType,
                            skia.AlphaType.kPremul_AlphaType)
    surface=skia.Surface.MakeRasterDirect(info,pixels,WIDTH*4)
    canvas=surface.getCanvas()
    canvas.scale(2,2)
    timebase=Fraction(1,FPS)
    codec=os.environ.get('ELYSIAN_INTERMEDIATE_ENCODER','libx264')
    if codec not in ('libx264','h264_qsv'):
        raise ValueError('Intermediate encoder must be libx264 or h264_qsv')
    with av.open(str(target), mode='w', options={'movflags':'+faststart'}) as container:
        stream=container.add_stream(codec,rate=FPS)
        stream.width,stream.height=WIDTH,HEIGHT
        stream.pix_fmt='nv12' if codec=='h264_qsv' else 'yuv420p'
        stream.codec_context.thread_count=threads
        stream.codec_context.gop_size=60
        stream.codec_context.max_b_frames=2
        stream.options=({'preset':'fast','global_quality':'12','profile':'high'} if codec=='h264_qsv'
                        else {'preset':preset,'crf':'16','profile':'high'})
        for i in range(count):
            draw(canvas,i)
            frame=av.VideoFrame.from_ndarray(pixels,format='bgra')
            frame.pts,frame.time_base=i,timebase
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
