struct S {
    unsigned char pad0[0x4c];
    unsigned int flags;
    unsigned char pad1[0x14];
    unsigned char bytes[4];
};

extern "C" void func_6063fd8c(S *self, unsigned int idx, unsigned char value)
{
    if (idx > 3u)
        return;

    self->flags |= 0x10u;
    self->bytes[idx] = value;
}