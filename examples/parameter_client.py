from cap_inspector import CapInspectorClient


def main():
    client = CapInspectorClient(host="10.170.10.55", port=50051)

    client.set_parameters(
        {
            "angle_limit": 3.0,
            "threshold_val": 210,
            "min_aspect_ratio": 1.9,
            "smooth_frames": 3,
        }
    )

    print(client.get_parameters())
    client.close()


if __name__ == "__main__":
    main()
