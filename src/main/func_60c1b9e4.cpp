struct Copy {
    char pad0[4];
    unsigned f4;
    unsigned f8;
    unsigned fc;
    unsigned f10;
    unsigned f14;
    unsigned f18;
    unsigned f1c;
    unsigned f20;
    unsigned f24;
    unsigned f28;
};

extern "C" void func_60c1b9e4(Copy *dst, Copy *src) {
    *((unsigned *)((char *)dst + 0x4)) = *((unsigned *)((char *)src + 0x4));
    *((unsigned *)((char *)dst + 0x8)) = *((unsigned *)((char *)src + 0x8));
    *((unsigned *)((char *)dst + 0xc)) = *((unsigned *)((char *)src + 0xc));
    *((unsigned *)((char *)dst + 0x10)) = *((unsigned *)((char *)src + 0x10));
    *((unsigned *)((char *)dst + 0x14)) = *((unsigned *)((char *)src + 0x14));
    *((unsigned *)((char *)dst + 0x18)) = *((unsigned *)((char *)src + 0x18));
    *((unsigned *)((char *)dst + 0x1c)) = *((unsigned *)((char *)src + 0x1c));
    *((unsigned *)((char *)dst + 0x28)) = *((unsigned *)((char *)src + 0x28));
    *((unsigned *)((char *)dst + 0x20)) = *((unsigned *)((char *)src + 0x20));
    *((unsigned *)((char *)dst + 0x24)) = *((unsigned *)((char *)src + 0x24));
}