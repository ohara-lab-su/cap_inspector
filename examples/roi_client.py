from cap_inspector import CapInspectorClient


def main():
    client = CapInspectorClient(host="10.170.10.55", port=50051)

    client.set_parameters(
        {
            "roi_x_range": (0.30, 0.70),
            "roi_y_range": (0.00, 0.35),
        }
    )

    print(client.get_parameters())
    client.close()


if __name__ == "__main__":
    main()
