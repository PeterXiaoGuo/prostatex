import math
import numpy as np
import h5py
from .h5_query import get_lesion_info


class Centroid:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return '({}, {}, {})'.format(self.x, self.y, self.z)


def extract_lesion_2d(img, centroid_position, size=None, realsize=16, imagetype='ADC'):
    if imagetype == 'ADC':
        if size is None:
            sizecal = math.ceil(realsize / 2)
        else:
            sizecal = size
    else:
        sizecal = size
    x_start = int(centroid_position.x - sizecal / 2)
    x_end = int(centroid_position.x + sizecal / 2)
    y_start = int(centroid_position.y - sizecal / 2)
    y_end = int(centroid_position.y + sizecal / 2)

    if centroid_position.z < 0 or centroid_position.z >= len(img):
        return None

    img_slice = img[centroid_position.z]

    return img_slice[y_start:y_end, x_start:x_end]


def parse_centroid(ijk):
    coordinates = ijk.split(b" ")
    return Centroid(int(coordinates[0]), int(coordinates[1]), int(coordinates[2]))


def str_to_modality(in_str):
    modalities = ['ADC', 't2_tse_tra']
    for m in modalities:
        if m in in_str:
            return m
    
    return "NONE"

def get_train_data(h5_file, query_words, size_px=16):
    lesion_info = get_lesion_info(h5_file, query_words)

    X = []
    y = []
    lesion_attributes = []
    previous_patient = ''
    previous_modality = ''
    
    unique_patient_ids = []
    
    for infos, image in lesion_info:
        _, current_patient, current_modality = infos[0]['name'].split('/')
        current_modality = str_to_modality(current_modality)
        
        if current_patient == previous_patient and current_modality == previous_modality:
            print('Warning in {}: Found duplicate match for {}. Skipping...'
                  .format(get_train_data.__name__, current_patient))
            continue
        for lesion in infos:
            unique_patient_ids.append((lesion['patient_id'], lesion['fid']))
            
            centroid = parse_centroid(lesion['ijk'])
            lesion_img = extract_lesion_2d(image, centroid, size=size_px)
            if lesion_img is None:
                print('Warning in {}: ijk out of bounds for {}. No lesion extracted'
                      .format(get_train_data.__name__, lesion))
                continue

            X.append(lesion_img)

            lesion_attributes.append(lesion)

            y.append(lesion['ClinSig'] == b"TRUE")

        previous_patient = current_patient
        previous_modality = current_modality

    X_final = []
    y_final = []
    attr_final = []
    for patient_id, fid in unique_patient_ids:
        x_new = []
        y_new = 0
        for i in range(len(lesion_attributes)):
            attr = lesion_attributes[i]
            
            if attr['patient_id'] == patient_id and attr['fid'] == fid:
                x_new.append(X[i])
                y_new = y[i]
        
        if not len(x_new) == len(query_words):
            print("Missing modalities for patient %s" % patient_id)
            continue
        
        X_final.append(x_new)
        y_final.append(y_new)
        attr_final.append({'patient_id': patient_id, 'fid': fid})
        
    return np.asarray(X_final), np.asarray(y_final), np.asarray(attr_final)

if __name__ == "__main__":
    from matplotlib import pyplot as plt
    """ Example usage: """
    h5_file = h5py.File('C:\\Users\\Jeftha\\stack\\Rommel\\ISMI\\prostatex-train.hdf5', 'r')

    X, y, _ = get_train_data(h5_file, ['ADC'])

    print(y[0])
    print(attr[0])
    plt.imshow(X[0], cmap='gray')
    plt.show()
