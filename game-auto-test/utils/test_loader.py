
from config.loader import load_config
from proto.proto_hashmap import backpack


def test_loader():
    items = load_config(r"D:\Game101\Codex\game-auto-test\sql\item.xlsx.v75.sql")


    print(f"\n有效数据共 {len(items)} 条")

    #打印表头
    print("========== 字段名 =========")
    for k in items[0].keys():
        print(f" {k}")

    # 打印前3行
    print("\n=== 前3行数据 ===")
    for i, item in enumerate(items[:3]):
        print(f" 第{i + 1}行: id = {item.get('id')},"
              f" name = {item.get('name')},"
              f" backpack_id = {item.get('backpack_id')}")

    # 统计 backpack_id 有多少种不同的值
    backpack_ids = set()
    for item in items:
        bid = item.get('backpack_id')
        if bid is not None:
            backpack_ids.add(bid)

    print(f"\n背包ID有: {sorted(backpack_ids)}")
    print(f"共 {len(backpack_ids)} 个背包")