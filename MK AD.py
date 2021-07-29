# v- beta 0.2
import obspython as obs
from PIL import Image
from os import path, remove, system, mkdir
from time import sleep
from threading import Thread
from cv2 import imread, resize, IMREAD_GRAYSCALE
from numpy import array, savez_compressed
from datetime import datetime, timedelta
from configparser import ConfigParser

s = {'state': False, 'gui': False, 'dir': path.dirname(__file__)+'/bin', 'sp': ' '}
s.update({'config': s['dir']+'/config.ini', 'img': s['dir']+'/img-crop.png', 'data': s['dir']+'/data.npz', 'map': s['dir']+'/img-crop-map.png'})
c = ConfigParser()
c.read(s['config'])
if not path.exists(s['config']):
    mkdir(s['dir']), c.add_section('General'), system(f'attrib +h "{s["dir"]}"'), c.write(open(s['config'], 'w'))
    # DL play_btn + pause_btn + ico...
s.update({k: v for k, v in c.items('General')})


def config(k, v, section='General'):
    if k not in s.keys() or s[k] != v:
        s[k] = v
        with open(s['config'], 'w') as w:
            return c.set(section, k, v), c.write(w)


def set_src(name):
    if 'src' not in s.keys() or name != s['src']:
        src_obs = obs.obs_get_source_by_name(name)
        h, w = obs.obs_source_get_height(src_obs), obs.obs_source_get_width(src_obs)
        if h < 480:
            print('Please select a valid source')
        else:
            config('crop', str((round(w * 84.4 / 100), round(h * 77.3 / 100), round(w * 94.8 / 100), round(h * 95.8 / 100))))
            config('crop-map', str((round(w * 25 / 100), round(h * 89.56 / 100), round(w * 68.75 / 100), round(h * 94.6 / 100))))
            config('src', name)
            s['src_obs'] = src_obs
            return print(f'Source {name} selected')


def set_profile(p):
    prof_read = open(path.expanduser(f'~/AppData/Roaming/obs-studio/basic/profiles/{p}/basic.ini')).read()
    mode = (('FilePath=', '\nFileNameWithoutSpace=true'), ('RecFilePath=', 'RecFileNameWithoutSpace=true'))['Mode=Advanced' in prof_read]
    config('prof', p), config('p_rec', (path.expanduser('~/Videos'), prof_read.split(mode[0])[-1].split('\n'))[mode[0] in prof_read])
    if mode[1] in prof_read:
        config('sp', '_')
    else:
        with open(s['config'], 'w') as w:
            s['sp'] = ' '
            c.remove_option('General', 'sp'), c.write(w)
    if p != s['prof']:
        print(f'Current profile use: {p}')


set_profile(open(path.expanduser('~/AppData/Roaming/obs-studio/global.ini')).read().split('ProfileDir=')[1].split('\n')[0])
if 'src' in s.keys():
    s['src_obs'] = obs.obs_get_source_by_name(s['src'])


# Screenshot -----------------------------------------------------------------------------------------------------------
def main():
    if not s['state']:
        return
    obs.obs_frontend_take_source_screenshot(s['src_obs'])
    sleep(1)
    for sec in (1, 0):
        s['date'] = (datetime.now() - timedelta(seconds=sec)).strftime('%Y-%m-%d{sp}%H-%M-%S'.format_map(s))
        img = '{p_rec}/Screenshot{sp}{date}.png'.format_map(s)
        if path.exists(img):
            Image.open(img).crop(eval(s['crop'])).save(s['img']), Image.open(img).crop(eval(s['crop-map'])).save(s['map'])
            img_array = imread(s['img'], IMREAD_GRAYSCALE)
            new_array = array(resize(img_array, (50, 50))).reshape(-1, 50, 50, 1)
            savez_compressed(s['data'], new_array)                                      # Data To Be Send
            remove(s['img']), remove(img)                                               # , remove(s['data'])
            return print('◄•►'), after()
    return print("No image found (check if the source is activated or if it's in the current scene)"), after()


def play():
    if s['state']:
        s['state'] = False
        print('Script in pause')
    elif 'src' in s.keys():
        s['state'] = True
        print('Script running')
        return Thread(target=main).start()
    else:
        raise Exception('\n\n\tPLEASE SELECT A VALID SOURCE !\n')


def after(n=2):
    sleep(n)
    return main()


# OBS Script -----------------------------------------------------------------------------------------------------------
def script_description():
    return ('MK Auto-Detect est une IA permettant de detecter automatique les places ainsi que les maps sur le merveilleux jeux Maio Kart 8 Deluxe')


def script_update(settings):
    set_src(obs.obs_data_get_string(settings, 'source'))

    set_profile(open(path.expanduser('~/AppData/Roaming/obs-studio/global.ini')).read().split('ProfileDir=')[1].split('\n')[0])


def script_properties():
    props = obs.obs_properties_create()

    p = obs.obs_properties_add_list(props, 'source', 'Selectionner la source MK', obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    srcs = obs.obs_enum_sources()
    for src in srcs:
        name = obs.obs_source_get_name(src)
        if 'Audio' in name or 'Mic/Aux' in name:
            continue
        obs.obs_property_list_add_string(p, name, name)
    obs.source_list_release(srcs)
    obs.obs_properties_add_button(props, 'play', 'Play', lambda a, b: play())
    obs.obs_properties_add_button(props, 'pause', 'Pause', lambda a, b: play())

    return props
