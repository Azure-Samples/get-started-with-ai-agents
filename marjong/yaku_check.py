
# yaku_check.py 

import define
import player as player_module
from collections import Counter
from yakuman_check import check_yakuman

# --- helper utilities -------------------------------------------------
def _all_player_tiles(player):
    """
    門前の牌リストを返すヘルパー。

    - プレイヤーの手牌 (`player.hand`) のみを含む。
    - 和了牌（`player.add_tile`）があれば追加する。
    - 鳴き（`player.melds`）は「面子の構成が失われる」ため、含めない。

    役判定では面子の組み合わせが重要なため、
    鳴きを個別牌に展開せず、門前牌のみで判定する。
    """
    tiles = []
    # 手牌（門前）のコピーを扱う（元を破壊しないため）
    tiles.extend(getattr(player, 'hand', []).copy())
    # 和了牌があれば含める
    if getattr(player, 'add_tile', None):
        tiles.append(player.add_tile)
    # 鳴きは面子の構成が重要なため、展開して牌リストに加えない
    return tiles

def _concealed_tiles(player):
    """
    門前（鳴きのない部分）の牌を返すヘルパー。

    通常は `player.hand` と `player.add_tile`（あれば）を結合した一覧を返す。
    ピンフや一盃口など「門前限定」判定に使うための補助関数です。
    """
    tiles = getattr(player, 'hand', []).copy()
    if getattr(player, 'add_tile', None):
        tiles.append(player.add_tile)
    return tiles

def _is_numeric_tile(tile):
    """数牌かどうかを判定する（例: '5m', '2p'）。

    戻り値: True=数牌, False=字牌や不正な形式
    """
    return isinstance(tile, str) and len(tile) == 2 and tile[0].isdigit() and tile[1] in define.SUIT_ORDER

def _tile_suit_num(tile):
    """
    数牌を (数字, 種別) のタプルに変換するヘルパー。

    例: '5m' -> (5, 'm')
    非数牌の場合は (None, None) を返す。
    """
    if not _is_numeric_tile(tile):
        return None, None
    return int(tile[0]), tile[1]

def _tiles_counts(player):
    """プレイヤーの全牌の出現回数カウンタを返すヘルパー。"""
    return Counter(_all_player_tiles(player))


def _all_tiles_with_melds(player):
    """
    鳴き牌を含めた全牌のリストを返すヘルパー。

    - 手牌 (`player.hand`)
    - 和了牌 (`player.add_tile`) があれば追加
    - 鳴き (`player.melds`) があれば展開して追加
    役によって鳴きを含めるかどうかを切り替えられるようにするための補助関数
    """
    tiles = _all_player_tiles(player).copy()
    for meld in getattr(player, 'melds', []):
        if isinstance(meld, dict):
            tiles.extend(meld.get('meld', []))
        else:
            tiles.extend(meld)
    return tiles



def _can_form_standard_melds(hand):
    """
    手牌（14枚）が標準的な面子形式（4×4面子 + 1対子）で構成可能か判定するヘルパー。

    用途: ピンフ判定で「通常の面子形式であることを確認」する際に利用。
    戻り値: True=標準形式で構成可能、False=不可能
    """
    if len(hand) != 14:
        return False
    # 簡易チェック: 手牌に重複がないか、基本的なバリデーション
    # （完全な面子分解は複雑なため、ここは簡易実装）
    cnt = Counter(hand)
    # 最大で4枚までは可能（同一牌は最大4枚）
    return all(count <= 4 for count in cnt.values())


def _find_waits(hand, tsumo_tile=None):
    """
    手牌から「ツモ待ちの形」を検出するヘルパー。

    ツモ可能な待ち種別を返す:
    - '両面': 両面待ち（e.g., 3-4-5-6 で 3 or 6 で待ち）
    - '辺': 辺張待ち（e.g., 1-2 で 3 で待ち）
    - '嗣': 嗣張待ち（e.g., 1-3 で 2 で待ち）
    - '単': 単騎待ち（対子で 1 種類で待ち）

    簡易実装：完全な牌の組み合わせ分析は複雑なため、ここでは
    比較的単純なパターンを検出する。
    """
    if tsumo_tile:
        hand_with_tsumo = hand + [tsumo_tile]
    else:
        hand_with_tsumo = hand
    
    if len(hand_with_tsumo) != 14:
        return []
    
    cnt = Counter(hand_with_tsumo)
    waits = []
    
    # 簡易的な待ち判定: ツモ牌がある場合、その牌が何パターンに該当するかを判定
    # （完全な待ち形分解は省略し、基本的な判定のみ実装）
    if tsumo_tile:
        num, suit = _tile_suit_num(tsumo_tile)
        if num and suit:
            # 両面待ちパターン: n-n+1-n+2-... の形で中間を埋めるツモなら両面
            if num - 1 >= 1 and num + 1 <= 9:
                key_prev = f"{num-1}{suit}"
                key_curr = f"{num}{suit}"
                key_next = f"{num+1}{suit}"
                if key_prev in cnt and key_next in cnt:
                    waits.append('両面')
            # 単純な辺/嗣パターンも判定可（省略）
    
    return waits if waits else ['不確定']


def is_riichi(player_obj):  
    """立直 (リーチ) 判定"""  
    # リーチが成立する条件: 門前でテンパイしリーチ宣言している  
    return len(player_obj.melds) == 0 and player_obj.tsumo_tile is None  
  
def is_tsumo(player):  
    """門前清自摸和 (ツモ) 判定"""  
    # ツモが成立する条件: 門前で自摸和了している  
    return len(player.melds) == 0 and player.add_tile is not None and getattr(player, 'is_add_tsumo', False)
  
def is_pinfu(player):
    """
    平和 (ピンフ) 判定 - 1翻役

    条件:
    - 門前（副露なし）
    - 字牌を含まない（数牌のみ）
    - 両面待ち
    - 雀頭が役牌でない
    - 平和和了（ツモの場合は門前ツモが別役となるため注意）
    
    簡易実装: 両面待ち判定は基本的なパターンのみ対応。
    
    注意: 槓を含む場合、手牌総数が 14 を超えるため判定対象外とする。
    """
    # 副露があれば平和ではない（槓も副露の一種なので判定対象外）
    if len(player.melds) > 0:
        return False
    
    # 字牌が含まれる場合は平和ではない
    tiles = _all_player_tiles(player)
    if any(tile in define.HORNORS for tile in tiles):
        return False
    
    # 手牌が14枚であることを確認（槓がある場合は exclude）
    if len(tiles) != 14:
        return False
    if not _can_form_standard_melds(tiles):
        return False
    
    # 簡易的な両面待ち判定:
    # ツモ牌がある場合、ツモ牌で和了している局面を想定し、
    # その待ちが両面待ちであるかを確認する
    if player.add_tile:
        waits = _find_waits(player.hand, player.add_tile)
        if '両面' in waits:
            return True
    
    # ツモ牌がない場合は、門前で数牌のみなら簡易的にピンフと判定
    # （厳密な待ち判定は要改善）
    return True

  
def is_tanyao(player):
    """
    断么九 (タンヤオ) 判定
    
    タンヤオは副露を含むため、全牌（手牌 + 鳴き牌）で判定する。
    ただし面子の構成を考慮する必要があるため、鳴き牌も含める。
    """
    # 手牌とツモ牌
    all_tiles = _all_player_tiles(player)
    # 鳴き牌も含める（タンヤオは副露OK）
    for meld in getattr(player, 'melds', []):
        if isinstance(meld, dict):
            all_tiles.extend(meld.get('meld', []))
        else:
            all_tiles.extend(meld)
    
    for t in all_tiles:
        if _is_numeric_tile(t):
            num, _ = _tile_suit_num(t)
            if num < 2 or num > 8:
                return False
        else:
            # 字牌が混ざっていたらタンヤオではない
            return False
    return True

def is_iipeikou(player):
    """一盃口 (簡易判定): 門前かつ同一順子が2組ある場合を検出する簡易実装"""
    if len(player.melds) > 0:
        return False
    tiles = _concealed_tiles(player)
    # 集計: 各種別ごとに数牌のカウンタを作り、順子の出現数を数える
    for suit in define.SUIT_ORDER:
        nums = [int(t[0]) for t in tiles if _is_numeric_tile(t) and t[1] == suit]
        if not nums:
            continue
        cnt = Counter(nums)
        seq_total = 0
        for n in range(1, 8):
            seq_count = min(cnt.get(n, 0), cnt.get(n+1, 0), cnt.get(n+2, 0))
            seq_total += seq_count
        if seq_total >= 2:
            return True
    return False

def is_ikkitsuukan(player):
    """一気通貫 (イッキツウカン) 判定

    門前・副露で翻数が変わる役（門前:2翻, 副露:1翻）。
    手牌 + 鳴き牌を展開して、同一種別に 123,456,789 の順子がそれぞれ存在するかをチェックする。
    簡易実装では、数牌ごとのカウントから逐次的に順子を取り除く方法で判定する。
    """
    all_tiles = _all_tiles_with_melds(player)
    # 数牌のみを扱う
    for suit in define.SUIT_ORDER:
        nums = [int(t[0]) for t in all_tiles if _is_numeric_tile(t) and t[1] == suit]
        if not nums:
            continue
        cnt = Counter(nums)
        # Greedyで123,456,789を構成できるか確認
        possible = True
        for seq in [(1,2,3),(4,5,6),(7,8,9)]:
            # それぞれの数が最低1枚ずつ必要
            if not all(cnt.get(n,0) >= 1 for n in seq):
                possible = False
                break
            # 消費
            for n in seq:
                cnt[n] -= 1
        if possible:
            return True
    return False

def is_sanshoku_doujun(player):
    """三色同順 (サンショクドウジュン) 判定

    同じ数字の順子が3種の数牌（萬/筒/索）に存在する場合成立。
    門前/副露で翻数が変わることがあるため判定自体は鳴き牌を含めて行い、
    翻数は `YAKU_FAN` の定義を参照して差分を適用する。
    """
    all_tiles = _all_tiles_with_melds(player)
    # 各種別ごとに数字のカウントを作る
    suit_counters = {suit: Counter(int(t[0]) for t in all_tiles if _is_numeric_tile(t) and t[1] == suit) for suit in define.SUIT_ORDER}
    # n=1..7 の順子について、全ての種別に存在する n を探す
    for n in range(1, 8):
        if all(suit_counters[suit].get(n, 0) >= 1 and suit_counters[suit].get(n+1, 0) >= 1 and suit_counters[suit].get(n+2, 0) >= 1 for suit in define.SUIT_ORDER):
            return True
    return False


def is_sanankou(player):
    """三暗刻 (三つの暗刻) 判定

    門前で成立することが条件となる役。簡易実装として、
    門前部分（鳴きに含まれない牌群）に同一牌が3枚以上ある種類が
    3種類以上存在する場合に成立と判定する。
    七対子や明確に面子分解できないケースは別途除外する。
    """
    # 七対子なら三暗刻ではない
    if is_chiitoitsu(player):
        return False

    concealed = _concealed_tiles(player)
    # 門前牌が14枚でない場合でも、門前の刻子が存在すれば成立する可能性がある
    cnt = Counter(concealed)
    concealed_triplets = sum(1 for v in cnt.values() if v >= 3)
    return concealed_triplets >= 3


def is_chanta(player):
    """混全帯么九 (チャンタ) 判定

    条件（簡易実装）:
    - すべての面子・雀頭に数牌の1/9または字牌が含まれていること
    - 鳴きありでも成立（副露時は翻数が低くなる）

    実装上の簡易化:
    - 鳴き (player.melds) がある場合は各鳴き面子に端牌/字牌が含まれるか確認
    - 門前部分については、雀頭に端牌/字牌があることを最低条件とする
    - 完全な面子分解は行わないため一部の境界ケースは見逃す可能性がある
    """
    # 全牌（鳴き含む）を取得
    all_tiles = _all_tiles_with_melds(player)

    # 鳴きがある場合、各鳴き面子に端牌/字牌が含まれているか確認
    for meld in getattr(player, 'melds', []):
        meld_tiles = meld.get('meld', []) if isinstance(meld, dict) else meld
        if not any((t in define.HORNORS) or ( _is_numeric_tile(t) and _tile_suit_num(t)[0] in (1,9) ) for t in meld_tiles):
            return False

    # 門前部分の雀頭が端牌/字牌であることを最低条件とする
    concealed = _concealed_tiles(player)
    if len(concealed) < 2:
        return False
    counts = Counter(concealed)
    # 雀頭候補に端牌/字牌があるか
    pair_ok = any((t in define.HORNORS or (_is_numeric_tile(t) and _tile_suit_num(t)[0] in (1,9))) and c >= 2 for t, c in counts.items())
    if not pair_ok:
        return False

    # 全体に端牌/字牌がまったく含まれないなら否定
    if not any((t in define.HORNORS) or (_is_numeric_tile(t) and _tile_suit_num(t)[0] in (1,9)) for t in all_tiles):
        return False

    return True


def is_sanshoku_doukou(player):
    """三色同刻 (同じ数字の刻子が3種の数牌で揃う) 判定

    実装方針（簡易）:
    - 鳴きのポン/カンはそのまま刻子とみなす
    - 門前の刻子は同一牌が3枚以上あることで検出する
    - ある数字について、萬/筒/索 の全てで刻子が存在すれば成立と判定する
    """
    # 構成する刻子の有無を suit->num->bool で管理
    triplet_available = {suit: {n: False for n in range(1, 10)} for suit in define.SUIT_ORDER}

    # 鳴きの刻子（ポン/カン）を反映
    for meld in getattr(player, 'melds', []):
        meld_tiles = meld.get('meld', []) if isinstance(meld, dict) else meld
        # 同一牌が3枚以上なら刻子と判定
        try:
            if len(meld_tiles) >= 3 and all(t == meld_tiles[0] for t in meld_tiles[:3]):
                tile = meld_tiles[0]
                if _is_numeric_tile(tile):
                    num, suit = _tile_suit_num(tile)
                    triplet_available[suit][num] = True
        except Exception:
            pass

    # 門前の刻子を牌カウントから検出
    concealed = _concealed_tiles(player)
    cnt = Counter(concealed)
    for tile, c in cnt.items():
        if _is_numeric_tile(tile):
            num, suit = _tile_suit_num(tile)
            if c >= 3:
                triplet_available[suit][num] = True

    # すべての種別で刻子が存在する数字を探す
    for n in range(1, 10):
        if all(triplet_available[suit].get(n, False) for suit in define.SUIT_ORDER):
            return True
    return False

def is_toitoi(player):
    """対々和 (トイトイ) 判定 - 刻子手 (鳴き可)

    鳴きがある場合でも成立することが多いため、鳴き牌を含めた全牌で判定する。
    簡易実装: 展開した全牌をカウントして、面子が刻子/槓子中心であることを確認する。
    完全な面子分解は実装範囲外のため、鳴きにチーが含まれる場合は除外し、
    鳴きがすべてポン/カンのみなら対々和判定を行う。
    """
    # 鳴きにチーが含まれる場合は対々和ではない
    for meld in getattr(player, 'melds', []):
        # meldがdict形式の場合は type キーを使う想定
        if isinstance(meld, dict):
            if meld.get('type') == define.MELD_TYPE_CHI:
                return False
        else:
            # リスト形式で渡される鳴きは順子と仮定して除外
            # ここでは単純に長さ3の順子をチーとみなす
            # 実装保証されていない場合は安全側で除外
            # 例: ['1萬','2萬','3萬'] など
            # 判定は簡易なので、3つの数牌かつ連続している場合はチーとみなす
            try:
                nums = [int(t[0]) for t in meld if _is_numeric_tile(t)]
                if len(nums) >= 3 and max(nums) - min(nums) == 2:
                    return False
            except Exception:
                pass
    # 鳴きがすべてポン/カンか、鳴きがない場合は対々和の可能性あり
    # ここでは全牌を展開して、刻子中心か簡易判定
    tiles = _all_tiles_with_melds(player)
    cnt = Counter(tiles)
    # 刻子系が少なくとも3つ（＋雀頭1つ）を満たすかを簡易判定
    triplet_count = sum(1 for v in cnt.values() if v >= 3)
    # 七対子と混同しないように最低限の判定
    return triplet_count >= 4


def is_sankantsu(player):
    """三槓子 (三つの槓) 判定

    鳴き・暗槓を問わず、カンの面子が3つ以上存在する場合に成立と判定します。
    player.melds に格納された鳴き情報の 'type' を見て判定します。
    """
    kan_melds = [m for m in getattr(player, 'melds', []) if (isinstance(m, dict) and m.get('type') == define.MELD_TYPE_KAN) or (not isinstance(m, dict) and len(m) >= 4)]
    return len(kan_melds) >= 3


def is_honroutou(player):
    """混老頭 (混老頭) 判定

    全牌（手牌 + ツモ牌 + 鳴き牌）が端牌(1/9)または字牌のみで構成される場合に成立。
    簡易実装で全牌を展開して判定します。
    """
    tiles = _all_tiles_with_melds(player)
    allowed = set(define.CHINRO_TILES) | set(define.HORNORS)
    return all(t in allowed for t in tiles)


def is_double_riichi(player):
    """ダブルリーチ判定（簡易）

    実装上の簡易ルール:
    - `player.riichi_kawa_tile_no` が -1 でない（リーチ済み）
    - かつその捨て牌番号が最初の巡目（プレイヤー数以内）であることをもってダブルリーチと判定する

    厳密なゲーム進行情報がないため、第一巡の捨て牌（1〜4）でのリーチをダブルリーチと見なします。
    """
    no = getattr(player, 'riichi_kawa_tile_no', -1)
    if no is None or no < 0:
        return False
    try:
        return no <= len(define.SEATS)
    except Exception:
        return False

def is_haitei(tile_mountain):
    """
    海底撈月 (ハイテイ) 判定 - 1翻役
    
    牌山の最後の牌をツモして和了した場合に成立。
    tile_mountain の山牌状態を確認して判定する。
    
    条件: 山牌に残された牌がない、または最後の1枚のみ残っている
    """
    if tile_mountain is None:
        return False
    remaining_tiles = [tile for tile in tile_mountain.wall_tiles if not tile.get("is_dead_wall", False)]
    return len(remaining_tiles) <= 1

def is_houtei(tile_mountain):
    """
    河底撈魚 (ホウテイ) 判定 - 1翻役
    
    牌山が完全に枯れた状態で、捨て牌でロン和了した場合に成立。
    tile_mountain の山牌状態を確認して判定する。
    
    条件: 山牌が完全に枯れている（王牌のみ残っている）
    """
    if tile_mountain is None:
        return False
    remaining_tiles = [tile for tile in tile_mountain.wall_tiles if not tile.get("is_dead_wall", False)]
    return len(remaining_tiles) == 0

def is_rinshan_tsumo(player, is_kang_tsumo=False):
    """
    林荘ツモ (リンシャンツモ) 判定 - 1翻役
    
    槓（カン）の直後に嶺上牌をツモして和了した場合に成立。
    is_kang_tsumo フラグを受け取って判定する。
    
    条件: 槓の直後のツモで和了、かつ門前
    """
    if not is_kang_tsumo:
        return False
    # 槓後ツモは門前限定（副露がないか確認）
    return len(player.melds) == 0 and player.add_tile is not None and getattr(player, 'is_add_tsumo', False)

def is_yakuhai(player):
    """役牌判定"""
    # 役牌の条件: 三元牌または場風牌・自風牌の刻子/槓子がある
    winds_and_dragons = list(define.SANGEN_TILES) + [player.wind]
    for meld in player.melds:
        if meld[0] in winds_and_dragons and len(meld) >= 3:
            return True
    return False

# 役牌
def yakuhai_list(player):
    """
    役牌の列表示を返すヘルパー。
    
    役牌は主に鳴きで成立する役なので、手牌 + ツモ牌 + 鳴き牌をすべて含めて判定。
    """
    hand = player.hand.copy()
    if player.add_tile:
        hand.append(player.add_tile)
    for meld in getattr(player, 'melds', []):
        if isinstance(meld, dict):
            hand.extend(meld.get('meld', []))
        else:
            hand.extend(meld)
    counts = Counter(hand)
    # define.HORNORS は日本語の字牌セットを持つ
    return [h for h in define.HORNORS if counts.get(h, 0) >= 3]

# 七対子
def is_chiitoitsu(player):
    """
    七対子 (チーイツ) 判定
    
    七対子は門前限定の役なので、手牌 + ツモ牌のみで判定。
    鳴きがあれば七対子ではない。
    """
    if len(player.melds) > 0:
        return False
    hand = _concealed_tiles(player)
    if len(hand) != 14:
        return False
    counts = Counter(hand)
    return sorted(counts.values()) == [2] * 7

# 混一色
def is_honitsu(player):
    """
    混一色 (ホニツ) 判定: 数牌は同一種別＋字牌を含める。
    
    混一色は副露OKな役なので、手牌 + ツモ牌 + 鳴き牌をすべて含めて判定。
    """
    hand = player.hand.copy()
    if player.add_tile:
        hand.append(player.add_tile)
    for meld in getattr(player, 'melds', []):
        if isinstance(meld, dict):
            hand.extend(meld.get('meld', []))
        else:
            hand.extend(meld)
    suit_tiles = [tile for tile in hand if len(tile) == 2 and tile[1] in define.SUIT_ORDER]
    if not suit_tiles:
        return False
    suit = suit_tiles[0][1]
    return all((len(tile) == 2 and tile[1] == suit) or (tile in define.HORNORS) for tile in hand)

# 清一色
def is_chinitsu(player):
    """
    清一色 (チニツ) 判定: 数牌のみで同一種別のみで構成される。
    
    清一色は副露OKな役なので、手牌 + ツモ牌 + 鳴き牌をすべて含めて判定。
    """
    hand = player.hand.copy()
    if player.add_tile:
        hand.append(player.add_tile)
    for meld in getattr(player, 'melds', []):
        if isinstance(meld, dict):
            hand.extend(meld.get('meld', []))
        else:
            hand.extend(meld)
    suit_tiles = [tile for tile in hand if len(tile) == 2 and tile[1] in define.SUIT_ORDER]
    if not suit_tiles:
        return False
    suit = suit_tiles[0][1]
    return all(len(tile) == 2 and tile[1] == suit for tile in suit_tiles)

# 純全帯么九（じゅんちゃん）
def is_junchangtai(player):
    """
    純全帯么九 (じゅんちゃん) 判定 - 門前限定3翻役
    
    条件（簡易実装）:
    - 門前のみ（副露があれば成立しない）
    - 数牌は1/9のみで、すべての面子と雀頭に1/9が含まれている
    - 混全帯么九（チャンタ）と異なり、字牌が一切含まれない
    """
    # 副露があれば成立しない
    if len(player.melds) > 0:
        return False
    
    concealed = _concealed_tiles(player)
    if len(concealed) != 14:
        return False
    
    # 数牌のみで構成されている（字牌が混ざっていないか確認）
    for tile in concealed:
        if tile in define.HORNORS:
            return False
    
    # すべてのタイルが端牌（1/9）であるか確認
    # 完全な面子分解は複雑なため、簡易実装として
    # 牌に1/9が十分に含まれているかを確認する
    counts = Counter(concealed)
    endpoint_tiles = set(define.CHINRO_TILES)
    
    # 端牌のみで14枚を構成できるか簡易判定
    has_endpoints = any(tile in endpoint_tiles for tile in concealed)
    if not has_endpoints:
        return False
    
    # より厳密には、面子分解で全面子に端牌が含まれるか確認する必要があるが、
    # 簡易実装として、端牌が複数枚存在して、手牌全体が数牌のみなら成立と見なす
    endpoint_count = sum(1 for tile in concealed if tile in endpoint_tiles)
    return endpoint_count >= 5  # 最低限の端牌が存在することを確認

# 二盃口（りゃんぺいこう）
def is_ryanpeikou(player):
    """
    二盃口 (りゃんぺいこう) 判定 - 門前限定3翻役
    
    条件:
    - 門前のみ
    - 同一の順子が2組×2セット存在する（1盃口が2つある状態）
    - 例: 1-2-3, 1-2-3, 4-5-6, 4-5-6 など
    """
    # 副露があれば成立しない
    if len(player.melds) > 0:
        return False
    
    tiles = _concealed_tiles(player)
    if len(tiles) != 14:
        return False
    
    # 各種別ごとに数牌を集計し、順子の出現パターンを検出
    for suit in define.SUIT_ORDER:
        nums = [int(t[0]) for t in tiles if _is_numeric_tile(t) and t[1] == suit]
        if not nums:
            continue
        
        cnt = Counter(nums)
        
        # 同一の順子が2個以上あるか検出
        identical_seqs = []
        for n in range(1, 8):
            seq_count = min(cnt.get(n, 0), cnt.get(n+1, 0), cnt.get(n+2, 0))
            if seq_count >= 2:
                identical_seqs.append((n, seq_count))
        
        # 同一順子が2個以上の組が2つ以上存在すれば二盃口成立
        if len(identical_seqs) >= 2:
            return True
    
    return False

# 天和
def is_tenhou(is_parent, is_first_draw, is_tsumo):  
    # 親が配牌直後（第一自摸前）に和了（≒配牌即和了）  
    # is_parent: 親ならTrue  
    # is_first_draw: 第1ツモ前ならTrue  
    # is_tsumo: ツモ和了時True  
    return is_parent and is_first_draw and is_tsumo 

# 地和
def is_chiihou(is_parent, is_first_draw, is_tsumo):  
    # 子で第1自摸直後にツモ和了したら地和  
    # is_parent: 親ならFalse  
    # is_first_draw: 第1ツモ直後ならTrue  
    # is_tsumo: ツモ和了時True  
    return (not is_parent) and is_first_draw and is_tsumo 
# 人和
def is_renhou(is_parent, is_first_draw, is_ron):  
    # 子が第1自摸前にロン和了したら人和  
    # is_parent: 親ならFalse  
    # is_first_draw: 第1ツモ前ならTrue  
    # is_ron: ロン和了時True  
    return (not is_parent) and is_first_draw and is_ron  

# 一巡目あがり役満チェック
def check_yakuman_first_turn(is_parent, is_first_draw, is_tsumo, is_ron):
    yakuman_list = []  
    if is_tenhou(is_parent, is_first_draw, is_tsumo):  
        yakuman_list.append('天和')  
    if is_chiihou(is_parent, is_first_draw, is_tsumo):  
        yakuman_list.append('地和')  
    if is_renhou(is_parent, is_first_draw, is_ron):  
        yakuman_list.append('人和')  
    return yakuman_list

# 通常役チェック
def check_yaku(player, tile_mountain=None, is_kang_tsumo=False, is_win_tsumo=False, is_ron=False):
    """
    通常役（1翻〜複数翻）をチェックして役名リストと飜数を返す。
    
    引数:
      - player: Player オブジェクト
      - tile_mountain: TileMountain オブジェクト（ハイテイ・ホウテイ判定用、オプション）
      - is_kang_tsumo: 槓後ツモかどうか（林荘ツモ判定用）
      - is_win_tsumo: ツモで和了したかどうか
      - is_ron: ロンで和了したかどうか
    
    戻り値: (役名リスト, 飜数)
    """
    result = []
    fan = 0
    is_open = len(getattr(player, 'melds', [])) > 0
    
    # 1翻役チェック
    if is_pinfu(player):
        fan_value = define.YAKU_FAN.get('平和', 1)
        if fan_value > 0:
            result.append('平和')
            fan += fan_value
    if is_tanyao(player):
        fan_value = define.YAKU_FAN.get('断么九', 1)
        if fan_value > 0:
            result.append('断么九')
            fan += fan_value
    if is_iipeikou(player):
        fan_value = define.YAKU_FAN.get('一盃口', 1)
        if fan_value > 0:
            result.append('一盃口')
            fan += fan_value
    if is_win_tsumo and is_tsumo(player):
        fan_value = define.YAKU_FAN.get('門前清自摸和', 1)
        if fan_value > 0:
            result.append('門前清自摸和')
            fan += fan_value
    if is_haitei(tile_mountain) and is_win_tsumo:
        fan_value = define.YAKU_FAN.get('海底撈月', 1)
        if fan_value > 0:
            result.append('海底撈月')
            fan += fan_value
    if is_houtei(tile_mountain) and is_ron:
        fan_value = define.YAKU_FAN.get('河底撈魚', 1)
        if fan_value > 0:
            result.append('河底撈魚')
            fan += fan_value
    if is_rinshan_tsumo(player, is_kang_tsumo):
        fan_value = define.YAKU_FAN.get('林荘ツモ', 1)
        if fan_value > 0:
            result.append('林荘ツモ')
            fan += fan_value
    
    # 2翻役チェック（鳴きによる翻数変化に対応）
    # 対々和
    if is_toitoi(player):
        fan_value = define.YAKU_FAN.get('対々和', 2)
        if fan_value > 0:
            result.append('対々和')
            fan += fan_value
    
    # 一気通貫（門前:2翻, 副露:1翻）
    if is_ikkitsuukan(player):
        val = define.YAKU_FAN.get('一気通貫', 2)
        if isinstance(val, dict):
            fan_value = val['open'] if is_open else val['closed']
        else:
            fan_value = val
        if fan_value > 0:
            result.append('一気通貫')
            fan += fan_value
    
    # 三色同順（門前:2翻, 副露:1翻）
    if is_sanshoku_doujun(player):
        val = define.YAKU_FAN.get('三色同順', 2)
        if isinstance(val, dict):
            fan_value = val['open'] if is_open else val['closed']
        else:
            fan_value = val
        if fan_value > 0:
            result.append('三色同順')
            fan += fan_value
    
    # 三暗刻（門前で2翻）
    if is_sanankou(player):
        val = define.YAKU_FAN.get('三暗刻', 2)
        if isinstance(val, dict):
            fan_value = val['open'] if is_open else val['closed']
        else:
            fan_value = val
        if fan_value > 0:
            result.append('三暗刻')
            fan += fan_value
    
    # 混全帯么九（門前で2翻、鳴きで1翻）
    if is_chanta(player):
        val = define.YAKU_FAN.get('混全帯么九', 2)
        if isinstance(val, dict):
            fan_value = val['open'] if is_open else val['closed']
        else:
            fan_value = val
        if fan_value > 0:
            result.append('混全帯么九')
            fan += fan_value
    
    # 三色同刻（門前で2翻）
    if is_sanshoku_doukou(player):
        val = define.YAKU_FAN.get('三色同刻', 2)
        if isinstance(val, dict):
            fan_value = val['open'] if is_open else val['closed']
        else:
            fan_value = val
        if fan_value > 0:
            result.append('三色同刻')
            fan += fan_value
    
    # 三槓子
    if is_sankantsu(player):
        fan_value = define.YAKU_FAN.get('三槓子', 2)
        if fan_value > 0:
            result.append('三槓子')
            fan += fan_value
    
    # 混老頭
    if is_honroutou(player):
        fan_value = define.YAKU_FAN.get('混老頭', 2)
        if fan_value > 0:
            result.append('混老頭')
            fan += fan_value
    
    # ダブルリーチ（局進行情報に依存するため簡易判定）
    if is_double_riichi(player):
        fan_value = define.YAKU_FAN.get('ダブルリーチ', 2)
        if fan_value > 0:
            result.append('ダブルリーチ')
            fan += fan_value
    
    # 2翻役チェック
    if is_chiitoitsu(player):
        fan_value = define.YAKU_FAN.get('七対子', 2)
        if fan_value > 0:
            result.append('七対子')
            fan += fan_value
    
    # 3翻役チェック
    if is_honitsu(player):
        fan_value = define.YAKU_FAN.get('混一色', 3)
        if fan_value > 0:
            result.append('混一色')
            fan += fan_value
    
    # 純全帯么九（門前限定3翻）
    if is_junchangtai(player):
        val = define.YAKU_FAN.get('純全帯么九', 3)
        if isinstance(val, dict):
            fan_value = val['open'] if is_open else val['closed']
        else:
            fan_value = val
        if fan_value > 0:
            result.append('純全帯么九')
            fan += fan_value
    
    # 二盃口（門前限定3翻）
    if is_ryanpeikou(player):
        val = define.YAKU_FAN.get('二盃口', 3)
        if isinstance(val, dict):
            fan_value = val['open'] if is_open else val['closed']
        else:
            fan_value = val
        if fan_value > 0:
            result.append('二盃口')
            fan += fan_value
    
    # 6翻役チェック
    if is_chinitsu(player):
        fan_value = define.YAKU_FAN.get('清一色', 6)
        if fan_value > 0:
            result.append('清一色')
            fan += fan_value
    
    # 役牌チェック（1翻、複数の役牌は複数カウント）
    yakuhai = yakuhai_list(player)
    for honor in yakuhai:
        fan_value = define.YAKU_FAN.get('役牌', 1)
        if fan_value > 0:
            result.append(f'役牌({honor})')
            fan += fan_value
    
    # 役がない場合
    if not result:
        result.append('役なし')
    
    return result, fan

# 全役チェック
def check_all_yaku(player_obj, tile_mountain=None, is_parent=False, is_first_draw=False, is_kang_tsumo=False, is_win_tsumo=False, is_ron=False):
    """
    player_obj を受け取り、役満優先で全役を返す。
    
    引数:
      - player_obj: Player オブジェクト
      - tile_mountain: TileMountain オブジェクト（ハイテイ・ホウテイ判定用、オプション）
      - is_parent: 親かどうか
      - is_first_draw: 第1ツモ直後かどうか
      - is_kang_tsumo: 槓後ツモかどうか
      - is_win_tsumo: ツモで和了したかどうか
      - is_ron: ロンで和了したかどうか
    
    戻り値: (役リスト, 飜数または役満換算ファン)
    """
    yakuman_list = check_yakuman(player_obj)
    fan = 0
    if yakuman_list:
        # 一巡目役満（天和/地和/人和）を追加でチェック
        yakuman_list.extend(check_yakuman_first_turn(is_parent, is_first_draw, is_win_tsumo, is_ron))
        fan = 13 * len(yakuman_list)
        return yakuman_list, fan
    else:
        yaku_list, fan = check_yaku(player_obj, tile_mountain, is_kang_tsumo, is_win_tsumo, is_ron)  # 通常役
        if fan > 0:
            yakuman_list = check_yakuman_first_turn(is_parent, is_first_draw, is_win_tsumo, is_ron)
        if not yakuman_list:
            if fan >= 13:
                yakuman_list.append('数え役満')
        if yakuman_list:
            fan = 13 * len(yakuman_list)
            return yakuman_list, fan
        return yaku_list, fan