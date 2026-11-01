extern "C" {

struct S {
    unsigned char pad0[0x2a54];
    unsigned int  field;      // at +0x2a54
};

int func_60524adc(S *s, unsigned int idx)
{
    unsigned int word = *(unsigned int *)((char *)s + 0x2a54 + ((idx >> 5) << 2));
    unsigned int bit = (word >> (idx & 0x1f)) & 1u;
    return bit ? 1 : 0;
}

}