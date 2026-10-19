extern "C" void func_604d67a8(void *p, unsigned int value);

struct func_604d67a8_layout {
    unsigned char pad_000[0x164];
    unsigned int field_164;
    unsigned char pad_168[0x42];
    unsigned char field_1aa;
};

extern "C" void func_604d67a8(void *p, unsigned int value)
{
    func_604d67a8_layout *s = (func_604d67a8_layout *)p;
    s->field_164 = value;
    s->field_1aa = 0;
}