extern "C" {

struct S {
    unsigned char pad0[0x4];
    unsigned int f4;
    unsigned int f8;
    unsigned int fC;
    unsigned int f10;
    unsigned int f14;
    unsigned int f18;
    unsigned int f1C;
    unsigned int f20;
    unsigned int f24;
    unsigned int f28;
    unsigned int f2C;
    unsigned short f30;
    unsigned char pad32;
    unsigned char f32;
    unsigned char pad33;
    unsigned int f34;
    unsigned int f38;
    unsigned int f3C;
    unsigned int f40;
    unsigned int f44;
    unsigned char f48;
    unsigned char f49;
    unsigned char pad4A[0x2];
    unsigned int f4C;
    unsigned int f50;
    unsigned int f54;
    unsigned int f58;
};

void func_60c1c4a8(S *dst, S *src)
{
    unsigned char *d = (unsigned char *)dst;
    unsigned char *s = (unsigned char *)src;
    *(unsigned int *)(d + 0x4) = *(unsigned int *)(s + 0x4);
    *(unsigned int *)(d + 0x8) = *(unsigned int *)(s + 0x8);
    *(unsigned int *)(d + 0xc) = *(unsigned int *)(s + 0xc);
    *(unsigned int *)(d + 0x10) = *(unsigned int *)(s + 0x10);
    *(unsigned int *)(d + 0x14) = *(unsigned int *)(s + 0x14);
    *(unsigned int *)(d + 0x18) = *(unsigned int *)(s + 0x18);
    *(unsigned int *)(d + 0x1c) = *(unsigned int *)(s + 0x1c);
    *(unsigned int *)(d + 0x20) = *(unsigned int *)(s + 0x20);
    *(unsigned int *)(d + 0x24) = *(unsigned int *)(s + 0x24);
    *(unsigned int *)(d + 0x28) = *(unsigned int *)(s + 0x28);
    *(unsigned int *)(d + 0x2c) = *(unsigned int *)(s + 0x2c);
    *(unsigned short *)(d + 0x30) = *(unsigned short *)(s + 0x30);
    *(unsigned char *)(d + 0x32) = *(unsigned char *)(s + 0x32);
    *(unsigned int *)(d + 0x34) = *(unsigned int *)(s + 0x34);
    *(unsigned int *)(d + 0x38) = *(unsigned int *)(s + 0x38);
    *(unsigned int *)(d + 0x3c) = *(unsigned int *)(s + 0x3c);
    *(unsigned int *)(d + 0x40) = *(unsigned int *)(s + 0x40);
    *(unsigned int *)(d + 0x44) = *(unsigned int *)(s + 0x44);
    *(unsigned char *)(d + 0x48) = *(unsigned char *)(s + 0x48);
    *(unsigned char *)(d + 0x49) = *(unsigned char *)(s + 0x49);
    *(unsigned int *)(d + 0x4c) = *(unsigned int *)(s + 0x4c);
    *(unsigned int *)(d + 0x50) = *(unsigned int *)(s + 0x50);
    *(unsigned int *)(d + 0x54) = *(unsigned int *)(s + 0x54);
    *(unsigned int *)(d + 0x58) = *(unsigned int *)(s + 0x58);
}

}