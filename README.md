
|program|description|
|----|----|
|`capture_image.py`|USB webCamから画像を取得してJPEG画像として保存。保存先はconfig.pyのimage_dirで指定。"cam"ウインドウがアクティブになってる必要がある（マウスでクリック）|
|`register_faces.py`|JPEGイメージから顔を検出し、データベースに登録。データはJSONファイルとして、出席番号、氏名、顔の特徴ベクトルとともに保存される。イメージデータはimage_dir、データベースレコード(JSON)はdatabase_dirで指定(config.py)。JSONファイル作成後は元のJPEGファイルは必要ない（削除可能）|
|`thermometer.py`|体温測定プログラム。ESCキーで終了したときに測定結果を保存したEXCELファイルを作成|


|Manufacturer|PN|Description|Qty|
|----|----|----|----|
|Switch Science|SSCI-033954|Conta(tm) Thermography module - AMG8833|1|
|SparkFun|SFE-DEV-15795|Qwiic Pro Micro (USB-C, 5V/16MHz)|1|
|SparkFun|SFE-DEV-14495|Qwiic adapter|1|
|SparkFun|SFE-PRT-14426|Qwiic cable 50mm|1|
|*|*|USB webCam, FOV~60deg, >VGA|1|
