# Copyright 2023 The Kubric Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import numpy as np
import sys
import os
import kubric as kb
from kubric.renderer.blender import Blender as KubricRenderer
import random
import math

logging.basicConfig(level="INFO")

# --- create scene and attach a renderer to it


np.set_printoptions(threshold=sys.maxsize)

#you don't want objects inside each other, right?
# --- populate the scene with objects, lights, cameras

N_TESTS = 1
N_ANGLES = 4 #number of views for each scene

# source_path = os.getenv("SHAPENET_GCP_BUCKET", "gs://kubric-public/assets/ShapeNetCore.v2.json")
# shapenet = kb.AssetSource.from_manifest(source_path)

def obj_builder(typ, scale, position):
    if (typ == "Cube"):
        return kb.Cube(name="far{}".format(i), scale=scale, position=position, material=kb.PrincipledBSDFMaterial(color=kb.random_hue_color()))
    if (typ == "Sphere"):
        return kb.Sphere(name="far{}".format(i), scale=scale, position=position, material=kb.PrincipledBSDFMaterial(color=kb.random_hue_color()))
    raise Exception("Unrecognized object type")

def gen(i):
    objs = []
    while(len(objs) < 10):
        if (random.randint(0, 2) == 0):
            scale = (math.exp(np.random.normal(-1.5, 0.5)), math.exp(np.random.normal(-1.5, 0.5)), math.exp(np.random.normal(-1.5, 0.5)))
            if (min(scale) * 2 < max(scale)): #don't want boxes that are too lopsided
                continue
            position = (random.uniform(-1, 1), random.uniform(-1, 1), scale[2])
            best_scale = 1.0
            for old_obj in objs:
                old_pos = old_obj[2]
                old_scale = old_obj[1]
                best_scale = min(best_scale, 0.9 * max((abs(position[0] - old_pos[0]) - old_scale[0]) / scale[0], (abs(position[1] - old_pos[1]) - old_scale[1]) / scale[1]))
            if (best_scale >= 0.5):
                scale = (scale[0] * best_scale, scale[1] * best_scale, scale[2])
                objs.append(("Cube", scale, position))
        else:
            siz = math.exp(np.random.normal(-1.5, 0.5))
            scale = (siz, siz, siz)
            position = (random.uniform(-1, 1), random.uniform(-1, 1), scale[2])
            best_scale = 1.0
            for old_obj in objs:
                old_pos = old_obj[2]
                old_scale = old_obj[1]
                best_scale = min(best_scale, 0.9 * max((abs(position[0] - old_pos[0]) - old_scale[0]) / scale[0], (0.5 * abs(position[1] - old_pos[1]) - old_scale[1]) / scale[1]))
            if (best_scale >= 0.8): #don't want spheres that are too lopsided
                scale = (scale[0] * best_scale, scale[1] * best_scale, scale[2])
                objs.append(("Sphere", scale, position))

    for j in range(N_ANGLES):
        angle = np.random.uniform(2.0 * np.pi)
        camera_position = (3.0 * np.cos(angle), 3.0 * np.sin(angle))
        scene = kb.Scene(resolution=(256, 256))
        renderer = KubricRenderer(scene)
        scene += kb.Cube(name="floor", scale=(100, 100, 0.1), position=(0, 0, -0.1))
        scene += kb.DirectionalLight(name="sun", position=(-1, -0.5, 3),
                                    look_at=(0, 0, 0), intensity=1.5)
        scene += kb.PerspectiveCamera(name="camera", position=(camera_position[0], camera_position[1], 2),
                                    look_at=(0, 0, 0))
        for obj_spec in objs:
            obj = obj_builder(*obj_spec)
            scene += obj
            #this gets rid of shadows
            # obj_blender = obj.linked_objects[renderer]
            # obj_blender.cycles_visibility.shadow = False
        # --- render (and save the blender file)
        renderer.save_state("output/test/test{}_{}.blend".format(i, j))
        frame = renderer.render_still()

        # --- save the output as pngs
        kb.write_png(frame["rgba"], "output/test/test{}_{}.png".format(i, j))
        # print(frame["segmentation"])
        with open('output/test/test{}_{}segmentation.npy'.format(i, j), 'wb') as f:
            np.save(f, frame["segmentation"].squeeze())
        kb.write_palette_png(frame["segmentation"], "output/test/test{}_{}_segmentation.png".format(i, j))
        scale = kb.write_scaled_png(frame["depth"], "output/test/test{}_{}_depth.png".format(i, j))
        logging.info("Depth scale: %s", scale)

for i in range(N_TESTS):
    gen(i)