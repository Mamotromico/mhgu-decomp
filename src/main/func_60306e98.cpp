typedef struct {
    unsigned char pad[0x1378];
    unsigned int field;
} func_60306e98_t;

extern "C" void func_60306e98(func_60306e98_t *self, unsigned int value)
{
    self->field = value;
}