"""排行榜用例：查询榜单列表、查询单个榜单详情。"""
from api.rank_api import RankAPI, RankType
import pytest


ALL_RANK_TYPES = [
    RankType.GOLD_ALL,
    RankType.HERO_ALL,
    RankType.WARSHIP_ALL,
    RankType.GUILD_ALL,
    RankType.FLIGHT_ALL,
    RankType.PVP_ALL,
    RankType.BANQUET_ALL,
    RankType.MEDALBOSS_ALL,
    RankType.WORLDBOSS_ALL,
    RankType.GVG_SCORE,
    RankType.TEXAS_ALL,
    RankType.MOUNTAIN_HERO,
    RankType.MOUNTAIN_WARSHIP,
]


@pytest.mark.smoke
def test_query_ranking_list(game_client):
    """测试：批量查询多个榜单的第一名"""
    rank_api = RankAPI(game_client)

    query_ids = ALL_RANK_TYPES

    infos = rank_api.get_ranking_list(query_ids)

    assert len(infos) > 0, "所有榜单都没有数据"

    print(f"\n请求 {len(query_ids)} 个榜单，服务器返回 {len(infos)} 个")
    for i, info in enumerate(infos):
        assert info.v >= 0, f"第{i + 1}个榜单第一名分数不合法: {info.v}"
        rank_name = RankType.get_name(query_ids[i])
        player_name = info.role.name if info.HasField("role") else "无"
        score_text = f"{info.v}" if info.v > 0 else "0（榜单暂无数据）"
        print(f"  {rank_name}: 分数 = {score_text}, 玩家 = {player_name}")


# 只查3个有代表性的榜单
INFO_RANK_TYPES = [RankType.WARSHIP_ALL, RankType.PVP_ALL, RankType.GOLD_ALL]

@pytest.mark.smoke
@pytest.mark.parametrize("rank_type", INFO_RANK_TYPES, ids=lambda x: RankType.get_name(x))
def test_query_ranking_info(game_client, rank_type):
    """测试：查询单个榜单的完整排行（含我的排名），每个榜单独立测试"""
    rank_api = RankAPI(game_client)
    rank_name = RankType.get_name(rank_type)

    ranking_list, mine_rank, mine_score = rank_api.get_ranking_info(rank_type)

    # 榜单没开启/没数据就跳过
    if len(ranking_list) == 0:
        pytest.skip(f"{rank_name}暂无数据")

    print(f"\n{rank_name}共 {len(ranking_list)} 名玩家")
    print(f"我的排名: {mine_rank}, 我的分数: {mine_score}")

    # 断言
    assert ranking_list[0].v >= 0, f"{rank_name}第一名分数不合法: {ranking_list[0].v}"
    assert mine_rank >= 0, f"{rank_name}我的排名不合法: {mine_rank}"

    # 打印前3名
    for i, info in enumerate(ranking_list[:3]):
        player_name = info.role.name if info.HasField("role") else "无"
        print(f"  第{i+1}名: {player_name}, 分数={info.v}, 等级={info.role.lv}")



