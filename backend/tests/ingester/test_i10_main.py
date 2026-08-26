import asyncio
import json

import websockets

from ingester.main import measure_extra_topics, socket_loop

HANDSHAKE = '0{"sid":"x","upgrades":[],"pingInterval":25000,"pingTimeout":60000}'
T_PACKET = ('42["t",{"TD":"10/08/2026","FT":"13:08:56","SB":"ACV","FV":"100","LC":"S",'
            '"FMP":"42100.0","FCV":"1000.0","SM":"74027","AVO":"590000","AVA":"24983210000.0"}]')


def _args_of(sub_frame: str) -> list[str]:
    i = sub_frame.index("[")
    return json.loads(sub_frame[i:])[1]["data"]["args"]


def test_socket_loop_subscribes_receives_reconnects():
    async def scenario():
        state = {"connects": 0, "subs": []}
        got, resubbed = asyncio.Event(), asyncio.Event()

        async def handler(ws):
            state["connects"] += 1
            await ws.send(HANDSHAKE)
            await ws.send("40")
            msg = await ws.recv()                 # frame subscribe đầu
            state["subs"].append(msg)
            if state["connects"] == 1:
                await ws.send(T_PACKET)
                await asyncio.sleep(0.2)
                await ws.close()                  # ép rớt → client phải nối lại
            else:
                resubbed.set()
                await asyncio.sleep(5)

        packets = []

        def on_packet(raw):
            packets.append(raw)
            if raw == T_PACKET:
                got.set()

        reconnects = []
        async with websockets.serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            stop = asyncio.Event()
            task = asyncio.create_task(socket_loop(
                f"ws://127.0.0.1:{port}/", ["t:ACV", "i:ACV"], on_packet, stop,
                on_reconnect=lambda: reconnects.append(1), reconnect_delay_s=0.1))
            await asyncio.wait_for(got.wait(), 5)
            await asyncio.wait_for(resubbed.wait(), 5)
            stop.set()
            await asyncio.wait_for(task, 5)

        assert state["connects"] == 2                          # đã tự nối lại
        assert _args_of(state["subs"][0]) == ["t:ACV", "i:ACV"]
        assert _args_of(state["subs"][1]) == ["t:ACV", "i:ACV"]  # đăng ký lại TOÀN BỘ
        assert reconnects == [1]                               # đồng bộ lại state khi nối lại
        assert T_PACKET in packets
    asyncio.run(scenario())


def test_measure_extra_topics():
    t = measure_extra_topics(["41I1G8000"])
    assert "o10:41I1G8000" in t and "t_ol:41I1G8000" in t and "u:41I1G8000" in t
    assert len([x for x in t if x.endswith(":41I1G8000")]) == 20
    assert "pth:HOSE" in t and "pth:UPCOM" in t
