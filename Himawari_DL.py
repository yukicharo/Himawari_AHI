########################################### Himawari_DL.py ###################################################
# Created by Yuki Mizuno
# Last Updated: 2025/06/13
# Download Himawari-8/9 AHI TOA data from CEReS ftp server
# Based on this document "https://ceres.chiba-u.jp/geoland/wp-content/uploads/2022/09/JPGU2022ver1.3_0529.pdf"
##############################################################################################################

import wget  # wget モジュールの import
import bz2   # 解凍用モジュール
import os    # os モジュール

# FTPサーバー情報
FTP = "ftp://hmwr829gr.cr.chiba-u.ac.jp/gridded/FD/V20190123/"
B = "EXT"
b = "ext"
bno = 1

# 出力先ディレクトリの指定
output_dir = "/media/storage_3/original/ext_01"  # 必要に応じて変更してください

# 出力先ディレクトリが存在しない場合は作成
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 年、月、日、時間、分のループ
for y in range(2023, 2024):  # Year
    for m in range(1, 9):  # Month
        for d in range(1, 32):  # Day
            for h in range(1, 5):  # Hour
                for mi in range(0, 60, 10):  # Minute

                    # FTP URLの構築
                    tt = FTP + "{year:04}{month:02}/{band}/".format(year=y, month=m, band=B)

                    # 日付と時間のフォーマット
                    DATE = "{year:04}{month:02}{day:02}{hour:02}{min:02}".format(year=y, month=m, day=d, hour=h, min=mi)
                    fname = DATE + ".{band}.{bandno:02}.fld.geoss".format(band=b, bandno=bno)
                    fnamebz = fname + ".bz2"
                    ttt = tt + fnamebz

                    # 出力ファイルのパス
                    file_path = os.path.join(output_dir, fname)

                    # すでにファイルが存在する場合はスキップ
                    if os.path.exists(file_path):
                        print(f"File already exists, skipping: {file_path}")
                        continue  # 次のファイルに進む

                    print(f"Downloading: {ttt}")

                    try:
                        # データダウンロード
                        wget.download(ttt, os.path.join(output_dir, fnamebz))  # 出力先ディレクトリを指定

                        # 圧縮データの解凍
                        with bz2.BZ2File(os.path.join(output_dir, fnamebz), "rb") as zipfile:
                            data = zipfile.read()  # 圧縮データ読み込み
                            with open(file_path, "wb") as f:
                                f.write(data)  # 解凍データ書き出し

                        # 圧縮ファイルの削除
                        os.remove(os.path.join(output_dir, fnamebz))

                        print(f"Downloaded and extracted: {fname}")
                    
                    except Exception as e:
                        # エラーが発生した場合の処理（エラーメッセージの表示）
                        print(f"Error occurred for {fnamebz}: {e}")
                        continue  # 次のファイルに進む

print("Download and extraction completed.")
