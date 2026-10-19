typedef struct {
    unsigned char pad[0x494];
    unsigned int value;
} S;

extern "C" void func_60c65f9c(S* s, unsigned int a, unsigned int b) {
    s->value = (a & 0xFFFFu) | (b << 16);
}