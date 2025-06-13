######################################################3#### Himawari_DL.py #################################################################
# Created by Yuki Mizuno
# Last Updated: 2025/04/11
# Extract scope of AOI from Himawari-8/9 AHI and convert from DN to TOA reflectance (multipied by 100) using LUT (by CEReS)
# Based on this document "https://ceres.chiba-u.jp/geoland/wp-content/uploads/2022/09/JPGU2022ver1.3_0529.pdf"
# You have to prepare LUT file which can be downloaded from this URL: ftp://hmwr829gr.cr.chiba-u.ac.jp/gridded/FD/support/count2tbb_v102.tgz
############################################################################################################################################

import numpy as np
import glob
import os
import matplotlib.pyplot as plt
from osgeo import gdal

# ディレクトリの設定
#input_dir = '/mnt/storage_2/Himawari/original/ext_01'
input_dir = '/media/storage_3/original/ext_01'
LUT_dir = '/mnt/storage_2/Himawari/LUT/'

# ファイルのリスト
list_files = sorted(glob.glob(os.path.join(input_dir, '*.geoss')))

# 日本全体の範囲（緯度・経度）
(lat_min, lat_max, lon_min, lon_max) = (24, 46, 122, 149)

# データのリシェイプ
def reshape(file):
    dataDN = np.fromfile(file, dtype='>u2')  # Big-endian 16-bit unsigned integer
    if "ext" in file:
        dataDN = dataDN.reshape(24000, 24000)
    elif "vis" in file:
        dataDN = dataDN.reshape(12000, 12000)
    elif "tir" or "sir" in file:
        dataDN = dataDN.reshape(6000, 6000)
    else:
        print("There is no file match for pattern.")
        return None
    return dataDN

# LUT（Look-Up Table）を使ってデータを変換
def convert_LUT(dataDN, file):
    if "vis.01" in file:
        DN, tbb = np.loadtxt(LUT_dir + 'vis.01', unpack=True)
    elif "vis.02" in file:
        DN, tbb = np.loadtxt(LUT_dir + 'vis.02', unpack=True)
    elif "vis.03" in file:
        DN, tbb = np.loadtxt(LUT_dir + 'vis.03', unpack=True)
    elif "tir.01" in file:
        DN, tbb = np.loadtxt(LUT_dir + 'tir.01', unpack=True)
    elif "tir.02" in file:
        DN, tbb = np.loadtxt(LUT_dir + 'tir.02', unpack=True)
    elif "ext.01" in file:
        DN, tbb = np.loadtxt(LUT_dir + 'ext.01', unpack=True)
    else:
        print("There is no LUT file.")
        return None
    dataTBB = tbb[dataDN]  # LUTで変換後の物理量（輝度温度など）
    return dataTBB

# AOI（日本全体）の範囲を抽出
def extract_scope(dataTBB, lat_min, lat_max, lon_min, lon_max, file):
    if "ext" in file:
        resolution = 0.005
    elif "vis" in file:
        resolution = 0.01
    elif "tir" or "sir" in file:
        resolution = 0.02
    else:
        print("No file is available")
        return None

    # 緯度経度をピクセルインデックスに変換
    y_min = int((60 - lat_max) / resolution)
    y_max = int((60 - lat_min) / resolution)
    x_min = int((lon_min - 85.0) / resolution)
    x_max = int((lon_max - 85.0) / resolution)
        
    dataTBB_tc = dataTBB[y_min:y_max, x_min:x_max]  # 指定範囲を抽出

    if "ext" in file:
        dataTBB_tc = dataTBB_tc.reshape(2200, 2, 2700, 2).mean(-1).mean(1)  # 2x2平均化/500 m解像度で出力したい場合はコメントアウト
    else:
        print("You don't heve to reshape data.")
    
    return dataTBB_tc

# 出力ファイルを保存（GeoTIFF）
def save_file(file, dataTBB_tc):
    if "vis.01" in file:
        output_dir = "/media/storage_4/vis_01"
    elif "vis.02" in file:
        output_dir = "/media/storage_4/vis_02"
    elif "vis.03" in file:
        output_dir = "/media/storage_4/vis_03"
    elif "tir.01" in file:
        output_dir = "/media/storage_4/tir_01"
    elif "tir.02" in file:
        output_dir = "/media/storage_4/tir_02"
    elif "ext.01" in file:
        output_dir = "/media/storage_4/ext_01_1km"
    else:
        print("There is no file.")
        return

    os.makedirs(output_dir, exist_ok=True)

    # ファイル名（拡張子なし）を抽出
    filename = os.path.splitext(os.path.basename(file))[0]
    output_filepath = os.path.join(output_dir, filename + '.tif')

    # 既にファイルが存在する場合はスキップ
    if os.path.exists(output_filepath):
        print(f"File {output_filepath} already exists. Skipping.")
        return

    # データの形状を取得
    rows, cols = dataTBB_tc.shape

    # 新しいTIFFファイルを作成
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(output_filepath, cols, rows, 1, gdal.GDT_Float32)

    # ジオトランスフォームの設定（仮に0.01度の解像度とした場合）
    ulx = lon_min  # 左上のX座標（経度）
    uly = lat_max  # 左上のY座標（緯度）

    if "ext" in file:
        resolution = 0.01 #reshape後の解像度 (0.005→0.01)/500 m解像度で出力したいときはコメントアウト
    elif "vis" in file:
        resolution = 0.01
    elif "tir" or "sir" in file:
        resolution = 0.02
    else:
        print("No file is available")
        return None
    
    pixel_width = resolution  # ピクセル幅（経度方向）
    pixel_height = -resolution  # ピクセル高さ（緯度方向、南向きなので負）

    # ジオトランスフォームを設定
    dataset.SetGeoTransform([ulx, pixel_width, 0, uly, 0, pixel_height])

    # 座標系の設定
    dataset.SetProjection('EPSG:4326')  # WGS 84（経緯度座標系）

    # 各バンドにデータを書き込む
    band = dataset.GetRasterBand(1)
    band.WriteArray(dataTBB_tc)

    dataset.FlushCache()  # キャッシュをフラッシュしてファイルに書き込む
    print(f"File saved as {output_filepath}")

# メイン処理
for file in list_files:
    reshaped_data = reshape(file)  # ファイルをリシェイプ
    converted_data = convert_LUT(reshaped_data, file)  # LUT変換
    if converted_data is not None:
        extracted_data = extract_scope(converted_data, lat_min, lat_max, lon_min, lon_max, file)  # 日本全体の範囲を抽出
        if extracted_data is not None:
            save_file(file, extracted_data)  # GeoTIFFとして保存
