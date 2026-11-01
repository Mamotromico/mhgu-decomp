typedef unsigned char uint8_t;
typedef unsigned int uint32_t;

struct S {
    uint8_t pad0[0x50];
    uint32_t field50;
    uint8_t pad54[4];
    uint32_t field58;
    uint8_t pad5c[0x14];
    uint8_t field70;
    uint8_t pad71[3];
    uint32_t field74;
};

extern "C" void func_606b58b4(S *s, uint32_t value)
{
    s->field50 |= 2u;
    s->field58 = value;
    s->field70 = 0;
    s->field74 = 0;
}