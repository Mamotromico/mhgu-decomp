typedef struct {
    unsigned char pad0[0x4];
    unsigned int field4;
    unsigned short field8;
    unsigned short fieldA;
    unsigned short fieldC;
    unsigned short fieldE;
    unsigned short field10;
    unsigned short field12;
    unsigned short field14;
    unsigned short field16;
    unsigned short field18;
    unsigned short field1A;
    unsigned short field1C;
    unsigned short field1E;
    unsigned short field20;
    unsigned short field22;
    unsigned short field24;
    unsigned short field26;
    unsigned short field28;
    unsigned short field2A;
    unsigned short field2C;
    unsigned short field2E;
    unsigned short field30;
} S;

extern "C" void func_60030b3c(S *dst, const S *src)
{
    *(unsigned int *)((char *)dst + 0x4) = *(const unsigned int *)((const char *)src + 0x4);
    *(unsigned short *)((char *)dst + 0x8) = *(const unsigned short *)((const char *)src + 0x8);
    *(unsigned short *)((char *)dst + 0xa) = *(const unsigned short *)((const char *)src + 0xa);
    *(unsigned short *)((char *)dst + 0xc) = *(const unsigned short *)((const char *)src + 0xc);
    *(unsigned short *)((char *)dst + 0xe) = *(const unsigned short *)((const char *)src + 0xe);
    *(unsigned short *)((char *)dst + 0x10) = *(const unsigned short *)((const char *)src + 0x10);
    *(unsigned short *)((char *)dst + 0x12) = *(const unsigned short *)((const char *)src + 0x12);
    *(unsigned short *)((char *)dst + 0x14) = *(const unsigned short *)((const char *)src + 0x14);
    *(unsigned short *)((char *)dst + 0x16) = *(const unsigned short *)((const char *)src + 0x16);
    *(unsigned short *)((char *)dst + 0x18) = *(const unsigned short *)((const char *)src + 0x18);
    *(unsigned short *)((char *)dst + 0x1a) = *(const unsigned short *)((const char *)src + 0x1a);
    *(unsigned short *)((char *)dst + 0x1c) = *(const unsigned short *)((const char *)src + 0x1c);
    *(unsigned short *)((char *)dst + 0x1e) = *(const unsigned short *)((const char *)src + 0x1e);
    *(unsigned short *)((char *)dst + 0x20) = *(const unsigned short *)((const char *)src + 0x20);
    *(unsigned short *)((char *)dst + 0x22) = *(const unsigned short *)((const char *)src + 0x22);
    *(unsigned short *)((char *)dst + 0x24) = *(const unsigned short *)((const char *)src + 0x24);
    *(unsigned short *)((char *)dst + 0x26) = *(const unsigned short *)((const char *)src + 0x26);
    *(unsigned short *)((char *)dst + 0x28) = *(const unsigned short *)((const char *)src + 0x28);
    *(unsigned short *)((char *)dst + 0x2a) = *(const unsigned short *)((const char *)src + 0x2a);
    *(unsigned short *)((char *)dst + 0x2c) = *(const unsigned short *)((const char *)src + 0x2c);
    *(unsigned short *)((char *)dst + 0x2e) = *(const unsigned short *)((const char *)src + 0x2e);
    *(unsigned short *)((char *)dst + 0x30) = *(const unsigned short *)((const char *)src + 0x30);
}