import define
import player

class Kawa:
    def __init__(self):
        self.kawa_tiles = []
        self.kawa_tiles_no = 0

    # 河に捨て牌を追加
    def add_kawa_tiles(self, player, discard_tile):
        ''' 河に捨て牌を追加 '''
        # 捨て牌番号をインクリメント
        self.kawa_tiles_no += 1
        # 河に捨て牌を追加
        self.kawa_tiles.append({  
            "discard_tile": discard_tile,  
            "player_id": player.id, 
            "called_by": None, 
            "call_type": None,
            "riichi" : False,
            "kawa_tiles_no": self.kawa_tiles_no,
            })

    # 最新の河牌にリーチフラグを付与
    def riichi_last_kawa_tile(self, player):
        ''' 最新の河牌にリーチフラグを付与 '''
        if self.kawa_tiles:
            if self.kawa_tiles[-1]["player_id"] == player.id:
                self.kawa_tiles[-1]["riichi"] = True
                player.riichi_kawa_tile_no = self.kawa_tiles[-1]["kawa_tiles_no"]
                return True
            else:
                print("最新の河牌は指定プレイヤーの捨て牌ではありません。処理を中断します。")
        else:
            print("河牌が存在しません。処理を中断します。")

        return False

    # 最新の河牌を取得
    def get_last_kawa_tile(self):
        ''' 最新の河牌を取得 '''
        if self.kawa_tiles:
            return self.kawa_tiles[-1]["discard_tile"]
        return None

    # 最新の河牌情報を更新
    def update_last_kawa_tile(self, player, called_by = None, call_type = None):
        ''' 最新の河牌情報を更新 '''
        if self.kawa_tiles:
            if not self.kawa_tiles[-1]["player_id"] == player.id:
                self.kawa_tiles[-1]["called_by"] = called_by
                self.kawa_tiles[-1]["call_type"] = call_type
                return True
            else:
                print("最新の河牌は指定プレイヤーの捨て牌です。処理を中断します。")
        else:
            print("河牌が存在しません。処理を中断します。")

        return False
        
    # チョンボ牌チェック
    def check_chonbo(self, player, add_tile):
        """ チョンボ牌チェック """
        for kawa_tile in self.kawa_tiles:
            if not kawa_tile["player_id"] == player.id:
                if kawa_tile["kawa_tiles_no"] < player.riichi_kawa_tile_no:
                    continue    # プレイヤー以外はリーチ前の捨て牌は無視
            # チョンボ牌かチェック
            if kawa_tile["discard_tile"] == add_tile:
                return True

        return False
