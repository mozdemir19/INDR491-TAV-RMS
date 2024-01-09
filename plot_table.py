import plotly.express as px
import numpy as np

interlacing = np.concatenate([np.linspace(1.0, 0.5, num=960), np.linspace(0.5, 1.0, num=960)])
im = np.zeros((1080, 1920))

for i in range(im.shape[0]):
    im[i,:] = interlacing

fig = px.imshow(im, color_continuous_scale='ylgnbu_r')
fig.show()