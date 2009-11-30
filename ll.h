#ifndef LL_LL_H
#define LL_LL_H

#include <stdbool.h>

struct ll_lens_t
{
    double x, y, mass;
};

struct ll_lenses_t
{
    unsigned num_lenses;
    struct ll_lens_t *lens;
};

struct ll_rect_t
{
    double x0, y0, x1, y1;
};

struct ll_magpattern_param_t
{
    struct ll_lenses_t lenses;
    struct ll_rect_t region;
    unsigned xpixels, ypixels;
    double pixels_per_width, pixels_per_height;
};

extern void
ll_init_magpattern_params(struct ll_magpattern_param_t *params,
                          struct ll_lenses_t *lenses,
                          struct ll_rect_t *region,
                          unsigned xpixels, unsigned ypixels);

struct ll_rayshooter_t
{
    struct ll_magpattern_param_t *params;
    unsigned levels;
    int refine;
    int refine_final;
    bool cancel;
};

extern void
ll_init_rayshooter(struct ll_rayshooter_t *rs,
                   struct ll_magpattern_param_t *params, unsigned levels);

extern void
ll_cancel_rayshooter(struct ll_rayshooter_t *rs);

extern bool
ll_shoot_single_ray(struct ll_magpattern_param_t *params,
                    double x, double y, double *mag_x, double *mag_y);

extern void
ll_rayshoot_rect(struct ll_magpattern_param_t *params, int *magpat,
                 const struct ll_rect_t *rect, int xrays, int yrays);

extern void
ll_rayshoot(struct ll_rayshooter_t *rs, int *magpat, struct ll_rect_t *rect,
            int xrays, int yrays, double *progress);

extern void
ll_ray_hit_pattern(struct ll_magpattern_param_t *params, char *buf,
                   struct ll_rect_t *rect);

extern void
ll_source_images(struct ll_magpattern_param_t *params, char *buf,
                 struct ll_rect_t *rect, int xrays, int yrays, int refine,
                 double source_x, double source_y, double source_r);

extern void
ll_image_from_magpat(char *buf, int *magpat, unsigned size);

extern void
ll_light_curve(struct ll_magpattern_param_t *params, int *magpat,
               double *curve, unsigned num_points,
               double x0, double y0, double x1, double y1);

#endif
