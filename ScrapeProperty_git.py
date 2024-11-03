# 不動産のWEBサイトからテキスト情報と画像のスクレイピングを行う

import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import time
import json
import unicodedata

# テキストファイルからカンマ区切りの駅名を読み込んでリストに変換
with open('search_station.txt', 'r', encoding='utf-8') as file:
    stations = [s.strip() for s in file.read().split(',') if s.strip()]


# ログインのためのURLとデータ
login_url = "https://example-real-estate-site.com/accounts/login"
login_data = {
    "data[Account][loginid]": "example_loginid",
    "data[Account][password]": "example_pass",
    '_method': 'POST'
}

# セッションを開始してログインする
with requests.Session() as session:
    # ログインページにPOSTリクエストを送信する
    response = session.post(login_url, data=login_data)

    # レスポンスの内容を確認
    if response.ok:
        print("ログインに成功しました。")
    else:
        print("ログインに失敗しました。")

    for station_name in stations:
        print(f"{station_name}の物件を検索します。")

        # 駅名をURLエンコードする
        station_name_encoded = urllib.parse.quote(station_name)

        # 駅名に基づいた検索URLを構築する
        search_url = f'https://example-real-estate-site.com/search?keyword=&station_keyword={station_name_encoded}'

        # BeautifulSoupでHTMLを解析する
        response = session.get(search_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # 物件リストを取得する
        property_ids = []
        for table in soup.find_all('table', class_='row js-room'):
            data_id = table.get('data-id')
            if data_id:
                property_ids.append(data_id)
        print(f"{station_name}の物件数: {len(property_ids)}")

        if property_ids:  # 物件のリストが空でない場合
            station_dir = f'scrape_result/{station_name}'
            os.makedirs(station_dir, exist_ok=True)  # 駅名のディレクトリを作成
        else:  # 物件のリストが空の場合
            print("物件がないためスキップします。")
            continue  # 次のループへ

        for idx, property_id in enumerate(property_ids):
            print(f"物件情報を取得中: {idx + 1}/{len(property_ids)}")

            # 物件詳細ページへのリンクを構築する
            detail_url = "https://example-real-estate-site.com/detail/" + property_id

            # 詳細ページにアクセスして情報を取得する
            detail_response = session.get(detail_url)
            detail_soup = BeautifulSoup(detail_response.content, 'html.parser')

            # 物件名を取得
            title = detail_soup.find('h2', class_='title sticky-element').text.strip()

            # 家賃を抽出
            rent = detail_soup.find('div', class_='price').find('span', class_='integer').text.strip() + \
                   detail_soup.find('div', class_='price').find('span', class_='decimal').text.strip() + "万円"

            # 基本情報のテーブルを取得
            info_basic = detail_soup.find('div', class_='info-basic')
            transportation_info = info_basic.find_all('td')

            # 交通、バス徒歩、敷金礼金、間取り・専有面積をそれぞれ抽出
            transportation = transportation_info[0].text.strip()
            bus_walk = transportation_info[1].text.strip()
            deposit_and_key_money = transportation_info[2].text.strip()
            floor_plan_area = transportation_info[3].text.strip()

            # 余分なスペースやタブを削除する
            transportation = ' '.join(transportation.split())
            bus_walk = ' '.join(bus_walk.split())
            deposit_and_key_money = ' '.join(deposit_and_key_money.split())
            floor_plan_area = ' '.join(floor_plan_area.split())
            title = unicodedata.normalize('NFKC', title)
            bus_walk = unicodedata.normalize('NFKC', bus_walk)
            deposit_and_key_money = unicodedata.normalize('NFKC', deposit_and_key_money)
            floor_plan_area = unicodedata.normalize('NFKC', floor_plan_area)

            # 所在地、設備の抽出
            building_table = detail_soup.find('table', id="building-summary")
            address_row = building_table.find('th', string='所在地')
            address = address_row.find_next('td').text.strip()
            facilities_row = building_table.find('th', string='設備')
            facilities = facilities_row.find_next('td').text.strip()

            walk = bus_walk.split()[-1]
            floor_plan = floor_plan_area.split()[0]
            area = floor_plan_area.split()[1]
            facilities = facilities.split('、')


            image_urls = []
            image_big = detail_soup.find_all('div', class_='image-big')
            for img_div in image_big:
                a_tag = img_div.find('a', class_='lightbox')
                if a_tag and 'href' in a_tag.attrs:
                    img_url = a_tag['href']
                    image_urls.append(img_url)

            image_list = detail_soup.find('div', class_='image-list')
            for a_tag in image_list.find_all('a', class_='lightbox'):
                if 'href' in a_tag.attrs:
                    img_url = a_tag['href']
                    image_urls.append(img_url)

            # 物件情報をJSON形式で保存
            base_info = {
                "物件名": title,
                "家賃": rent,
                "交通": transportation,
                "バス 徒歩": bus_walk,
                "敷金 礼金": deposit_and_key_money,
                "間取り 専有面積": floor_plan_area,
                "所在地": address,
                "設備": facilities
            }

            # テキスト情報を保存
            if base_info:
                output_dir = f'scrape_result/{station_name}/propety_{idx + 1}'
                os.makedirs(output_dir, exist_ok=True)
            else:  # 空の場合
                continue  # 次のループへ


            # 物件情報をJSON形式で保存
            property_data = {}

            image1_data = {
                "image1": {
                    "picture": "picture/picture_1.jpg",
                    "intro": "物件紹介",
                    "station": station_name + "駅",
                    "walk": walk,
                    "location": address,
                },
            }
            property_data.update(image1_data)

            if len(facilities) > 4:
                image2_data = {
                    "image2": {
                        "picture": "picture/picture_3.jpg",
                        "features": [
                            "専有面積 " + area,
                            facilities[0],
                            facilities[1],
                            facilities[2],
                            facilities[3],
                            facilities[4]
                        ],
                        "comment": f"comment1",
                        "layout": floor_plan
                    },
                }
                property_data.update(image2_data)

            if len(image_urls) > 3 and len(facilities) > 9:
                image3_data = {
                    "image3": {
                        "picture1": "picture/picture_2.jpg",
                        "picture2": "picture/picture_4.jpg",
                        "features": [
                            facilities[5],
                            facilities[6],
                            facilities[7],
                            facilities[8],
                            facilities[9]
                        ],
                        "comment": f"comment2",
                    },
                }
                property_data.update(image3_data)

            if len(image_urls) > 6 and len(facilities) > 14:
                image4_data = {
                    "image4": {
                        "picture1": "picture/picture_5.jpg",
                        "picture2": "picture/picture_6.jpg",
                        "picture3": "picture/picture_7.jpg",
                        "features": [
                            facilities[10],
                            facilities[11],
                            facilities[12],
                            facilities[13],
                            facilities[14]
                        ],
                        "comment": f"comment3",
                    },
                }
                property_data.update(image4_data)

            json_filename = os.path.join(output_dir, f'template_property_{idx + 1}.json')
            with open(json_filename, 'w', encoding='utf-8') as json_file:
                json.dump(property_data, json_file, ensure_ascii=False, indent=4)

            # 画像を保存
            if image_urls:  # 画像のリストが空でない場合にディレクトリを作成して保存する

                # 各URLから画像をダウンロードして保存
                for idx, url in enumerate(image_urls):
                    try:
                        url = "https://example-real-estate-site.goweb.work" + url

                        # 画像をダウンロード
                        response = session.get(url)
                        response.raise_for_status()  # エラーチェック

                        # ファイル名を決定
                        image_filename = os.path.join(output_dir, f"picture_{idx + 1}.jpg")

                        # 画像をファイルに書き込む
                        with open(image_filename, 'wb') as file:
                            file.write(response.content)

                        # サーバー負荷軽減のため待機時間を挿入
                        wait_time = 0.1  # 単位: 秒
                        time.sleep(wait_time)

                    except requests.exceptions.RequestException as e:
                        print(f"Failed to download image from {url}: {e}")
            else:
                print("画像がないためスキップします。")


            # サーバー負荷軽減のため待機時間を挿入
            wait_time = 1.0  # 単位: 秒
            time.sleep(wait_time)

    print("全ての物件の情報取得が完了しました。")
