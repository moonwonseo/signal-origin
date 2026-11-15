"""Per-node 30-day rainfall and temperature z-scores vs prior years (existing V1-V4 method, unchanged)."""
import sys, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from signal_origin.weather import rebuild_features
SRC = sys.argv[1]; OUT = sys.argv[2]
def one(rid):
    d = pd.read_csv(SRC, parse_dates=["weather_date_utc"])
    g = d[d.region_id.eq(rid)].set_index("weather_date_utc").sort_index()
    g = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
    z, _ = rebuild_features(g[["precipitation_mm_per_day", "temperature_mean_c", "temperature_min_c"]],
                            years_to_build=range(2007, 2027))
    return rid, z[["rain_anom_z", "temp_anom_z"]]
if __name__ == "__main__":
    ids = sorted(pd.read_csv(SRC, usecols=["region_id"]).region_id.unique())
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(one, ids))
    rain = pd.DataFrame({k: v.rain_anom_z for k, v in res.items()})
    temp = pd.DataFrame({k: v.temp_anom_z for k, v in res.items()})
    rain.index.name = temp.index.name = "weather_date_utc"
    rain.to_csv(OUT + "/rain_z.csv"); temp.to_csv(OUT + "/temp_z.csv")
    print(rain.dropna().shape, temp.dropna().shape, rain.dropna().index.min(), rain.dropna().index.max())
