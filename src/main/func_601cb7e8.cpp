extern "C" int func_601cb7e8(const void *obj, unsigned int idx, unsigned char *out)
{
    const unsigned char *p = (const unsigned char *)obj;
    unsigned int v;

    v = *(const unsigned short *)(p + 0x8);
    if ((v & 0x7f) == idx) {
        *out = (unsigned char)(v >> 8);
        return 1;
    }
    v = *(const unsigned short *)(p + 0xa);
    if ((v & 0x7f) == idx) {
        *out = (unsigned char)(v >> 8);
        return 1;
    }
    v = *(const unsigned short *)(p + 0xc);
    if ((v & 0x7f) == idx) {
        *out = (unsigned char)(v >> 8);
        return 1;
    }
    v = *(const unsigned short *)(p + 0xe);
    if ((v & 0x7f) != idx)
        return 0;
    *out = (unsigned char)(v >> 8);
    return 1;
}