struct S {
    unsigned char pad0[0x14];
    unsigned short field14;
    unsigned char pad1[0x5c - 0x14 - sizeof(unsigned short)];
    unsigned short field5c;
};

extern "C" unsigned short func_6131e87c(const S *s) {
    unsigned short b = ((const volatile S *)s)->field5c;
    unsigned short a = ((const volatile S *)s)->field14;
    return a - b;
}