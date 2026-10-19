struct Layout_6006d250 {
    unsigned char pad[0xcaf4];
    unsigned char field;
};

extern "C" int func_6006d250(const Layout_6006d250* p) {
    return p->field & 1;
}