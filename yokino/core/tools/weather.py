"""天气查询工具"""

from urllib.parse import quote

import requests

from core.tools.base import Tool


class WeatherTool(Tool):
    name = "get_weather"
    description = "查询指定城市的天气信息"

    def execute(self, city: str) -> str:
        # wttr.in 在中国可能不稳定，但有备选
        try:
            return self._fetch_wttr(city)
        except Exception:
            pass

        return f"暂时无法获取 {city} 的天气信息，请稍后再试。"

    def _fetch_wttr(self, city: str) -> str:
        url = f"https://wttr.in/{quote(city)}?format=j1&lang=zh"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")

        data = resp.json()
        current = data.get("current_condition", [{}])[0]

        temp = current.get("temp_C", "?")
        humidity = current.get("humidity", "?")
        desc = current.get("weatherDesc", [{}])[0].get("value", "未知")
        wind = current.get("winddir16Point", "?") + " " + current.get("windspeedKmph", "?") + "km/h"
        feels_like = current.get("FeelsLikeC", "?")

        return (
            f"{data['nearest_area'][0]['areaName'][0]['value']} ({data['nearest_area'][0]['country'][0]['value']})\n"
            f"🌡 温度: {temp}°C (体感 {feels_like}°C)\n"
            f"💧 湿度: {humidity}%\n"
            f"🌤 天气: {desc}\n"
            f"💨 风速: {wind}"
        )

    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如 Beijing, Shanghai, Tokyo"},
            },
            "required": ["city"],
        }
