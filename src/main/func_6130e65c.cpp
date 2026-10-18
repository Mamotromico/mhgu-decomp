typedef struct {
    unsigned char pad[0x5d9];
    unsigned char flag;
} func_6130e65c_t;

extern "C" unsigned int func_6130e65c(const func_6130e65c_t *p) {
    return p->flag >> 7;
}