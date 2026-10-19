struct Payload {
    unsigned char pad[0xca];
    unsigned char value;
};

extern "C" int func_610b1c80(const Payload* p) {
    return p->value != 0;
}