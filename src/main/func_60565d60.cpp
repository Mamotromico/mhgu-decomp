struct S_60565d60 {
    unsigned char pad[0x4c];
    volatile unsigned int flags;
    volatile unsigned char value;
};

extern "C" void func_60565d60(S_60565d60* s, unsigned char v)
{
    s->value = v;
    s->flags |= 4u;
}