"""扩充菜品数据库至550+道"""
import sqlite3, os, json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'canteen.db')
JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'dishes_data.json')

NEW_DISHES = {
    # ===== 鸡肉 chicken (17→34) +17 =====
    "chicken": [
        {"name": "盐焗鸡", "cuisine": "粤菜"},
        {"name": "白切鸡", "cuisine": "粤菜"},
        {"name": "豉油鸡", "cuisine": "粤菜"},
        {"name": "红烧鸡块", "cuisine": "家常"},
        {"name": "黄焖鸡", "cuisine": "鲁菜"},
        {"name": "咖喱鸡块", "cuisine": "东南亚"},
        {"name": "辣炒鸡块", "cuisine": "湘菜"},
        {"name": "干煸鸡", "cuisine": "川菜"},
        {"name": "左宗棠鸡", "cuisine": "湘菜"},
        {"name": "芙蓉鸡片", "cuisine": "鲁菜"},
        {"name": "柠香煎鸡排", "cuisine": "粤菜"},
        {"name": "可乐鸡翅", "cuisine": "家常"},
        {"name": "腰果鸡丁", "cuisine": "粤菜"},
        {"name": "麻辣鸡丝", "cuisine": "川菜"},
        {"name": "照烧鸡腿", "cuisine": "日式"},
        {"name": "红烧鸡爪", "cuisine": "家常"},
        {"name": "砂锅云吞鸡", "cuisine": "粤菜"},
    ],

    # ===== 鸭肉 duck (17→35) +18 =====
    "duck": [
        {"name": "北京烤鸭", "cuisine": "北方菜"},
        {"name": "酱板鸭", "cuisine": "湘菜"},
        {"name": "甜皮鸭", "cuisine": "川菜"},
        {"name": "香辣鸭块", "cuisine": "川菜"},
        {"name": "蚝油焖鸭", "cuisine": "粤菜"},
        {"name": "萝卜烧鸭", "cuisine": "家常"},
        {"name": "冬瓜焖鸭", "cuisine": "粤菜"},
        {"name": "五香卤鸭", "cuisine": "家常"},
        {"name": "陈皮鸭", "cuisine": "粤菜"},
        {"name": "泡椒鸭胗", "cuisine": "川菜"},
        {"name": "蒜香烤鸭腿", "cuisine": "粤菜"},
        {"name": "干煸鸭丝", "cuisine": "川菜"},
        {"name": "血鸭", "cuisine": "湘菜"},
        {"name": "红烧鸭翅", "cuisine": "家常"},
        {"name": "姜葱焖鸭", "cuisine": "粤菜"},
        {"name": "酸梅鸭", "cuisine": "粤菜"},
        {"name": "红烧鸭腿", "cuisine": "家常"},
        {"name": "仔姜爆鸭", "cuisine": "川菜"},
    ],

    # ===== 牛肉 beef (17→35) +18 =====
    "beef": [
        {"name": "番茄牛腩煲", "cuisine": "家常"},
        {"name": "萝卜牛腩煲", "cuisine": "粤菜"},
        {"name": "清炖牛肉", "cuisine": "西北菜"},
        {"name": "麻辣牛肉片", "cuisine": "川菜"},
        {"name": "豉椒牛肉", "cuisine": "粤菜"},
        {"name": "铁板牛肉", "cuisine": "粤菜"},
        {"name": "滑蛋牛肉", "cuisine": "粤菜"},
        {"name": "牙签牛肉", "cuisine": "湘菜"},
        {"name": "干锅牛肉", "cuisine": "川菜"},
        {"name": "蚝油牛肉", "cuisine": "粤菜"},
        {"name": "酱牛肉", "cuisine": "北方菜"},
        {"name": "杭椒牛柳", "cuisine": "家常"},
        {"name": "水煮牛柳", "cuisine": "川菜"},
        {"name": "沙茶牛肉", "cuisine": "粤菜"},
        {"name": "啤酒牛肉", "cuisine": "家常"},
        {"name": "蒜薹炒牛肉", "cuisine": "家常"},
        {"name": "苦瓜炒牛肉", "cuisine": "粤菜"},
        {"name": "红烧牛筋", "cuisine": "鄂菜"},
    ],

    # ===== 鱼肉 fish (14→30) +16 =====
    "fish": [
        {"name": "红烧带鱼", "cuisine": "北方菜"},
        {"name": "豆豉蒸鱼", "cuisine": "粤菜"},
        {"name": "蒜子焖鱼块", "cuisine": "粤菜"},
        {"name": "番茄鱼片", "cuisine": "川菜"},
        {"name": "糟溜鱼片", "cuisine": "鲁菜"},
        {"name": "西湖醋鱼", "cuisine": "浙菜"},
        {"name": "雪菜黄鱼", "cuisine": "苏菜"},
        {"name": "孜然烤鱼", "cuisine": "西北菜"},
        {"name": "酸辣鱼片", "cuisine": "湘菜"},
        {"name": "豉汁蒸鱼头", "cuisine": "粤菜"},
        {"name": "干炸小黄鱼", "cuisine": "北方菜"},
        {"name": "香煎马鲛鱼", "cuisine": "粤菜"},
        {"name": "蒜蓉烤鱼", "cuisine": "川菜"},
        {"name": "醋溜鱼块", "cuisine": "鲁菜"},
        {"name": "剁椒蒸鱼", "cuisine": "湘菜"},
        {"name": "葱姜焗鱼", "cuisine": "粤菜"},
    ],

    # ===== 虾 shrimp (14→30) +16 =====
    "shrimp": [
        {"name": "龙井虾仁", "cuisine": "浙菜"},
        {"name": "芙蓉虾仁", "cuisine": "鲁菜"},
        {"name": "干烧明虾", "cuisine": "川菜"},
        {"name": "豉油皇大虾", "cuisine": "粤菜"},
        {"name": "避风塘炒虾", "cuisine": "粤菜"},
        {"name": "清炒虾仁", "cuisine": "苏菜"},
        {"name": "番茄虾仁", "cuisine": "家常"},
        {"name": "咖喱虾", "cuisine": "东南亚"},
        {"name": "翡翠虾仁", "cuisine": "粤菜"},
        {"name": "金沙虾", "cuisine": "粤菜"},
        {"name": "蒜蓉粉丝蒸虾", "cuisine": "粤菜"},
        {"name": "油爆虾", "cuisine": "苏菜"},
        {"name": "椒盐濑尿虾", "cuisine": "粤菜"},
        {"name": "香煎虾饼", "cuisine": "粤菜"},
        {"name": "干烧虾仁", "cuisine": "川菜"},
        {"name": "盐水虾", "cuisine": "苏菜"},
    ],

    # ===== 羊肉 lamb (8→18) +10 =====
    "lamb": [
        {"name": "清炖羊肉", "cuisine": "西北菜"},
        {"name": "羊肉炖萝卜", "cuisine": "西北菜"},
        {"name": "红焖羊肉", "cuisine": "东北菜"},
        {"name": "孜然羊排", "cuisine": "西北菜"},
        {"name": "辣炒羊肉", "cuisine": "湘菜"},
        {"name": "蒜爆羊肉", "cuisine": "鲁菜"},
        {"name": "干锅羊肉", "cuisine": "川菜"},
        {"name": "羊肉手抓饭", "cuisine": "西北菜"},
        {"name": "羊肉烩菜", "cuisine": "西北菜"},
        {"name": "红烧羊排", "cuisine": "西北菜"},
    ],

    # ===== 其他荤菜 otherMeat (64→99) +35 =====
    "otherMeat": [
        {"name": "干豆角烧肉", "cuisine": "湘菜", "protein": "pork"},
        {"name": "板栗烧排骨", "cuisine": "粤菜", "protein": "pork"},
        {"name": "年糕烧排骨", "cuisine": "苏菜", "protein": "pork"},
        {"name": "蒜香排骨", "cuisine": "粤菜", "protein": "pork"},
        {"name": "孜然排骨", "cuisine": "西北菜", "protein": "pork"},
        {"name": "酸菜炖排骨", "cuisine": "东北菜", "protein": "pork"},
        {"name": "冬瓜炖排骨", "cuisine": "粤菜", "protein": "pork"},
        {"name": "海带烧排骨", "cuisine": "鲁菜", "protein": "pork"},
        {"name": "腐乳烧肉", "cuisine": "粤菜", "protein": "pork"},
        {"name": "雪菜肉丝", "cuisine": "苏菜", "protein": "pork"},
        {"name": "烂肉豇豆", "cuisine": "川菜", "protein": "pork"},
        {"name": "榨菜肉丝", "cuisine": "川菜", "protein": "pork"},
        {"name": "芹菜肉丝", "cuisine": "家常", "protein": "pork"},
        {"name": "茭白肉丝", "cuisine": "苏菜", "protein": "pork"},
        {"name": "糖醋肉段", "cuisine": "东北菜", "protein": "pork"},
        {"name": "鱼香排骨", "cuisine": "川菜", "protein": "pork"},
        {"name": "粉蒸肥肠", "cuisine": "川菜", "protein": "pork"},
        {"name": "干煸肥肠", "cuisine": "川菜", "protein": "pork"},
        {"name": "卤水拼盘", "cuisine": "粤菜", "protein": "pork"},
        {"name": "麻辣香锅", "cuisine": "川菜", "protein": "pork"},
        {"name": "干煸肉丝", "cuisine": "川菜", "protein": "pork"},
        {"name": "冬瓜烧肉丸", "cuisine": "粤菜", "protein": "pork"},
        {"name": "红烧肘子", "cuisine": "鲁菜", "protein": "pork"},
        {"name": "东坡肘子", "cuisine": "川菜", "protein": "pork"},
        {"name": "香芋扣肉", "cuisine": "粤菜", "protein": "pork"},
        {"name": "红烧肥肠", "cuisine": "川菜", "protein": "pork"},
        {"name": "腊肉炒豆干", "cuisine": "湘菜", "protein": "pork"},
        {"name": "土豆红烧肉", "cuisine": "家常", "protein": "pork"},
        {"name": "冬瓜烧排骨", "cuisine": "粤菜", "protein": "pork"},
        {"name": "苦瓜烧排骨", "cuisine": "粤菜", "protein": "pork"},
        {"name": "蒜薹炒腊肉", "cuisine": "湘菜", "protein": "pork"},
        {"name": "毛豆炒肉末", "cuisine": "苏菜", "protein": "pork"},
        {"name": "虎皮蛋烧肉", "cuisine": "家常", "protein": "pork"},
        {"name": "腐竹烧排骨", "cuisine": "粤菜", "protein": "pork"},
        {"name": "西芹炒肉片", "cuisine": "家常", "protein": "pork"},
    ],

    # ===== 素菜 vegetable (117→157) +40 =====
    "vegetable": [
        {"name": "蒜蓉蒸丝瓜", "cuisine": "粤菜"},
        {"name": "蚝油草菇", "cuisine": "粤菜"},
        {"name": "清炒木耳菜", "cuisine": "家常"},
        {"name": "素炒平菇", "cuisine": "家常"},
        {"name": "红烧冬瓜", "cuisine": "家常"},
        {"name": "清炒西葫芦", "cuisine": "家常"},
        {"name": "蒜蓉炒豆角", "cuisine": "家常"},
        {"name": "素烧腐竹", "cuisine": "家常"},
        {"name": "芹菜炒木耳", "cuisine": "家常"},
        {"name": "酸辣藕丁", "cuisine": "川菜"},
        {"name": "糖醋藕片", "cuisine": "鲁菜"},
        {"name": "炒地瓜叶", "cuisine": "家常"},
        {"name": "清炒豌豆尖", "cuisine": "川菜"},
        {"name": "蒜蓉炒苋菜", "cuisine": "粤菜"},
        {"name": "上汤苋菜", "cuisine": "粤菜"},
        {"name": "腐乳空心菜", "cuisine": "粤菜"},
        {"name": "干锅包菜", "cuisine": "湘菜"},
        {"name": "酸辣魔芋", "cuisine": "川菜"},
        {"name": "素炒香菇", "cuisine": "家常"},
        {"name": "韭菜炒豆芽", "cuisine": "家常"},
        {"name": "剁椒蒸金针菇", "cuisine": "湘菜"},
        {"name": "蒜蓉烤茄子", "cuisine": "粤菜"},
        {"name": "金沙南瓜", "cuisine": "粤菜"},
        {"name": "香辣土豆丁", "cuisine": "川菜"},
        {"name": "葱油芋艿", "cuisine": "苏菜"},
        {"name": "油焖笋", "cuisine": "苏菜"},
        {"name": "榄菜肉末炒豆角", "cuisine": "粤菜"},
        {"name": "山药炒木耳", "cuisine": "家常"},
        {"name": "玉米粒炒松仁", "cuisine": "东北菜"},
        {"name": "凉拌金针菇", "cuisine": "家常"},
        {"name": "清炒茭白", "cuisine": "苏菜"},
        {"name": "素炒牛肝菌", "cuisine": "粤菜"},
        {"name": "红烧芋头", "cuisine": "家常"},
        {"name": "雪菜炒豆瓣", "cuisine": "苏菜"},
        {"name": "水煮豆腐", "cuisine": "川菜"},
        {"name": "卤水豆腐", "cuisine": "粤菜"},
        {"name": "香煎豆腐", "cuisine": "家常"},
        {"name": "蟹黄豆腐", "cuisine": "苏菜"},
        {"name": "蒜苗炒千张", "cuisine": "家常"},
        {"name": "竹笋炒木耳", "cuisine": "家常"},
    ],

    # ===== 汤 soup (39→58) +19 =====
    "soup": [
        {"name": "冬瓜薏米汤", "cuisine": "粤菜"},
        {"name": "马蹄胡萝卜汤", "cuisine": "粤菜"},
        {"name": "莲藕花生汤", "cuisine": "粤菜"},
        {"name": "枸杞猪肝汤", "cuisine": "粤菜"},
        {"name": "皮蛋瘦肉粥汤", "cuisine": "粤菜"},
        {"name": "酸辣豆腐汤", "cuisine": "川菜"},
        {"name": "西湖牛肉羹", "cuisine": "浙菜"},
        {"name": "疙瘩汤", "cuisine": "北方菜"},
        {"name": "白菜粉丝汤", "cuisine": "北方菜"},
        {"name": "萝卜粉丝汤", "cuisine": "家常"},
        {"name": "豆腐菌菇汤", "cuisine": "家常"},
        {"name": "西红柿鸡蛋汤", "cuisine": "家常"},
        {"name": "胡辣汤", "cuisine": "西北菜"},
        {"name": "番茄排骨汤", "cuisine": "川菜"},
        {"name": "海带排骨汤", "cuisine": "粤菜"},
        {"name": "酸菜肉丝汤", "cuisine": "川菜"},
        {"name": "皮蛋黄瓜汤", "cuisine": "川菜"},
        {"name": "香菜豆腐汤", "cuisine": "家常"},
        {"name": "紫菜豆腐汤", "cuisine": "家常"},
    ],

    # ===== 面食/主食 noodle (42→60) +18 =====
    "noodle": [
        {"name": "肉夹馍", "cuisine": "西北菜"},
        {"name": "凉皮", "cuisine": "西北菜"},
        {"name": "馄饨", "cuisine": "苏菜"},
        {"name": "红糖糍粑", "cuisine": "川菜"},
        {"name": "鸡蛋灌饼", "cuisine": "北方菜"},
        {"name": "干炒牛河", "cuisine": "粤菜"},
        {"name": "星洲炒米", "cuisine": "东南亚"},
        {"name": "排骨面", "cuisine": "川菜"},
        {"name": "红烧牛肉面", "cuisine": "川菜"},
        {"name": "三鲜炒饭", "cuisine": "家常"},
        {"name": "雪菜肉丝面", "cuisine": "苏菜"},
        {"name": "番茄鸡蛋面", "cuisine": "家常"},
        {"name": "葱油花卷", "cuisine": "北方菜"},
        {"name": "兰州拉面", "cuisine": "西北菜"},
        {"name": "biangbiang面", "cuisine": "西北菜"},
        {"name": "煎饼果子", "cuisine": "北方菜"},
        {"name": "烧卖", "cuisine": "粤菜"},
        {"name": "叉烧包", "cuisine": "粤菜"},
    ],
}


def insert_new_dishes():
    conn = sqlite3.connect(DB_PATH)

    # 先列出现有菜品名
    cur = conn.execute("SELECT name FROM dishes")
    existing = {row[0] for row in cur.fetchall()}

    total_added = 0
    skipped = 0

    for category, dishes in NEW_DISHES.items():
        for dish in dishes:
            if dish["name"] in existing:
                skipped += 1
                continue
            protein = dish.get("protein", "")
            try:
                conn.execute(
                    "INSERT INTO dishes (name, category, cuisine, protein) VALUES (?,?,?,?)",
                    (dish["name"], category, dish["cuisine"], protein)
                )
                total_added += 1
            except sqlite3.IntegrityError:
                skipped += 1

    conn.commit()
    conn.close()

    print(f"新增 {total_added} 道菜品，跳过 {skipped} 道（已存在）")
    return total_added


def update_json():
    """同步更新 dishes_data.json"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT name, category, cuisine, protein FROM dishes WHERE enabled=1 ORDER BY id")

    data = {}
    for row in cur.fetchall():
        cat = row[1]
        if cat not in data:
            data[cat] = []
        entry = {"name": row[0], "cuisine": row[2]}
        if row[3]:
            entry["protein"] = row[3]
        data[cat].append(entry)

    conn.close()

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {JSON_PATH}")


def print_summary():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT category, COUNT(*) FROM dishes GROUP BY category ORDER BY COUNT(*) DESC")
    rows = cur.fetchall()
    total = sum(r[1] for r in rows)

    print(f"\n===== 菜品分类汇总（总计: {total} 道）=====")
    for cat, cnt in rows:
        print(f"  {cat}: {cnt}")

    cur = conn.execute("SELECT cuisine, COUNT(*) FROM dishes GROUP BY cuisine ORDER BY COUNT(*) DESC")
    print(f"\n===== 菜系汇总 =====")
    for cuisine, cnt in cur.fetchall():
        print(f"  {cuisine}: {cnt}")

    conn.close()


if __name__ == "__main__":
    print("开始扩充菜品数据库...")
    added = insert_new_dishes()
    update_json()
    print_summary()
    print(f"\n扩充完成！新增 {added} 道菜品。")
