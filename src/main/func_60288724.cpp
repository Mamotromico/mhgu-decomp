struct Data_60288724 {
    unsigned char pad[0x2464];
    unsigned short value;
};

extern "C" void func_60288724(Data_60288724 *p) {
    p->value |= 5;
}