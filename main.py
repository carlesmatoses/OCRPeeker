from ocrpeeker.daemon import main
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

if __name__ == "__main__":
    main()
