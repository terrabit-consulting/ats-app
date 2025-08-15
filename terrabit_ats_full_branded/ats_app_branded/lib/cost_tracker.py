import json, os, datetime
PRICING = {
  "chat":{"gpt-4o":{"in_per_1k":0.005,"out_per_1k":0.015},"gpt-4o-mini":{"in_per_1k":0.00015,"out_per_1k":0.0006}},
  "whisper-1":0.006,
  "tts":{"gpt-4o-mini-tts":0.015}
}
DEFAULT_EXRATE = 4.60
def _mk(): d=datetime.datetime.utcnow(); return f"{d.year:04d}-{d.month:02d}"
class CostTracker:
    def __init__(self, store_path="cost_log.json", exrate_myr_per_usd=DEFAULT_EXRATE):
        self.store_path=store_path; self.exrate=exrate_myr_per_usd; self._data={"monthly":{}}
        if os.path.exists(store_path):
            try: self._data=json.load(open(store_path,"r",encoding="utf-8"))
            except: self._data={"monthly":{}}
    def _save(self):
        try: json.dump(self._data, open(self.store_path,"w",encoding="utf-8"), indent=2)
        except: pass
    def reset_current_month(self):
        self._data["monthly"][_mk()]={"usd":0.0,"by_feature":{}}; self._save()
    def add_usd(self, usd, feature="general"):
        mk=_mk(); m=self._data["monthly"].setdefault(mk, {"usd":0.0,"by_feature":{}})
        m["usd"]+=float(usd); m["by_feature"][feature]=m["by_feature"].get(feature,0.0)+float(usd); self._save()
    def add_chat_cost(self, in_tok,out_tok,model="gpt-4o",feature="chat"):
        cfg=PRICING["chat"].get(model, PRICING["chat"]["gpt-4o"])
        usd=(in_tok/1000.0)*cfg["in_per_1k"]+(out_tok/1000.0)*cfg["out_per_1k"]; self.add_usd(usd,feature); return usd
    def add_tts_cost(self, chars, model="gpt-4o-mini-tts", feature="tts"):
        per1k=PRICING["tts"].get(model, PRICING["tts"]["gpt-4o-mini-tts"]); usd=(chars/1000.0)*per1k; self.add_usd(usd,feature); return usd
    def add_whisper_cost_from_minutes(self, minutes, feature="whisper"):
        usd=minutes*PRICING["whisper-1"]; self.add_usd(usd, feature); return usd
    def get_monthly_totals(self):
        m=self._data["monthly"].get(_mk(), {"usd":0.0,"by_feature":{}}); usd=m["usd"]
        return {"usd":usd,"myr":usd*self.exrate,"by_feature":{k:{"usd":v,"myr":v*self.exrate} for k,v in m["by_feature"].items()}}
