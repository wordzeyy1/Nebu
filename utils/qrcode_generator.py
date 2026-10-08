import qrcode
import tempfile


def generate_qr(network, address, amount):

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )

    qr.add_data(address)

    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    temp = tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False,
    )

    image.save(temp.name)

    return temp.name
