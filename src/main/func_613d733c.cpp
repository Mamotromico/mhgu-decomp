union U {
    unsigned int val;
    struct {
        unsigned int low : 31;
        unsigned int high : 1;
    } bits;
};

extern "C" unsigned int func_613d733c(unsigned int x) {
    union U u;
    u.val = x;
    u.bits.high = 0;
    return u.val;
}