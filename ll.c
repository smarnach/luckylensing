#include "ll.h"
#include <values.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

extern void
ll_init_magpattern_params(struct ll_magpattern_param_t *params,
                          struct ll_lenses_t *lenses,
                          struct ll_rect_t *region,
                          unsigned xpixels, unsigned ypixels)
{
    params->lenses.num_lenses = lenses->num_lenses;
    params->lenses.lens = lenses->lens;
    params->region.x = region->x;
    params->region.y = region->y;
    params->region.width = region->width;
    params->region.height = region->height;
    params->xpixels = xpixels;
    params->ypixels = ypixels;
    params->pixels_per_width = xpixels / region->width;
    params->pixels_per_height = ypixels / region->height;
}

extern void
ll_init_rayshooter(struct ll_rayshooter_t *rs,
                   struct ll_magpattern_param_t *params, unsigned levels)
{
    rs->params = params;
    rs->levels = levels;
    rs->refine = 15;
    rs->refine_final = 25;
    rs->cancel = false;
}

extern void
ll_cancel_rayshooter(struct ll_rayshooter_t *rs)
{
    rs->cancel = true;
}

extern bool __attribute__ ((hot))
ll_shoot_single_ray(struct ll_magpattern_param_t *params,
                    double x, double y, double *mag_x, double *mag_y)
{
    struct ll_lens_t *lens = params->lenses.lens;
    double x_deflected = x, y_deflected = y;
    for(unsigned i = 0; i < params->lenses.num_lenses; ++i)
    {
        double dx = x - lens[i].x;
        double dy = y - lens[i].y;
        double theta_squared = dx*dx + dy*dy;
        double deflection = lens[i].mass / theta_squared;
        x_deflected -= dx * deflection;
        y_deflected -= dy * deflection;
    }
    *mag_x = (x_deflected - params->region.x) * params->pixels_per_width;
    *mag_y = (y_deflected - params->region.y) * params->pixels_per_height;
    return (0 <= *mag_x && *mag_x < params->xpixels &&
            0 <= *mag_y && *mag_y < params->ypixels);
}

extern void
ll_rayshoot_rect(struct ll_magpattern_param_t *params, int *magpat,
                 const struct ll_rect_t *rect, int xrays, int yrays)
{
    double width_per_xrays = rect->width / xrays;
    double height_per_yrays = rect->height / yrays;
    double mag_x, mag_y;
    for (int j = 0; j < yrays; ++j)
        for (int i = 0; i < xrays; ++i)
            if (ll_shoot_single_ray(params,
                                    rect->x + i*width_per_xrays,
                                    rect->y + j*height_per_yrays,
                                    &mag_x, &mag_y))
                ++magpat[(int)mag_y*params->xpixels + (int)mag_x];
}

static void __attribute__ ((hot))
_ll_rayshoot_bilinear(struct ll_magpattern_param_t *params, int *magpat,
                      struct ll_rect_t *rect, int refine)
{
    double ul_x, ul_y, ur_x, ur_y, ll_x, ll_y, lr_x, lr_y;
    double x0 = rect->x;
    double y0 = rect->y;
    double x1 = rect->x + rect->width;
    double y1 = rect->y + rect->height;
    bool ul = ll_shoot_single_ray(params, x0, y0, &ul_x, &ul_y);
    bool ur = ll_shoot_single_ray(params, x1, y0, &ur_x, &ur_y);
    bool ll = ll_shoot_single_ray(params, x0, y1, &ll_x, &ll_y);
    bool lr = ll_shoot_single_ray(params, x1, y1, &lr_x, &lr_y);
    double inv_refine = 1.0/refine;
    double ldown_x = (ll_x - ul_x) * inv_refine;
    double ldown_y = (ll_y - ul_y) * inv_refine;
    double rdown_x = (lr_x - ur_x) * inv_refine;
    double rdown_y = (lr_y - ur_y) * inv_refine;
    double right_x = (ur_x - ul_x) * inv_refine;
    double right_y = (ur_y - ul_y) * inv_refine;
    double update_x = (rdown_x - ldown_x) * inv_refine;
    double update_y = (rdown_y - ldown_y) * inv_refine;
    double sx = ul_x;
    double sy = ul_y;
    if (ul && ur && ll && lr)
        for (int j = 0; j < refine; ++j)
        {
            double x = sx;
            double y = sy;
            for (int i = 0; i < refine; ++i)
            {
                ++magpat[(int)y*params->xpixels + (int)x];
                x += right_x;
                y += right_y;
            }
            sx += ldown_x;
            sy += ldown_y;
            right_x += update_x;
            right_y += update_y;
        }
    else
        for (int j = 0; j < refine; ++j)
        {
            double x = sx;
            double y = sy;
            int i = 0;
            while ((x < 0.0 || x >= params->xpixels ||
                    y < 0.0 || y >= params->ypixels) &&
                   i < refine)
            {
                x += right_x;
                y += right_y;
                ++i;
            }
            while (i < refine &&
                   x >= 0.0 && x < params->xpixels &&
                   y >= 0.0 && y < params->ypixels)
            {
                ++magpat[(int)y*params->xpixels + (int)x];
                x += right_x;
                y += right_y;
                ++i;
            }
            sx += ldown_x;
            sy += ldown_y;
            right_x += update_x;
            right_y += update_y;
        }
}

static void
_ll_rayshoot_recursively(struct ll_rayshooter_t *rs, int *magpat,
                         struct ll_rect_t *rect, int xrays, int yrays,
                         unsigned level, double *progress)
{
    if (rs->cancel)
        return;
    if (level)
    {
        double width_per_xrays = rect->width / xrays;
        double height_per_yrays = rect->height / yrays;
        int *hit = malloc((xrays+1)*(yrays+1) * sizeof(int));
        double mag_x, mag_y;
        double xpixels = rs->params->xpixels;
        double ypixels = rs->params->ypixels;
        for (int j = 0, m = 0; j <= yrays; ++j)
            for (int i = 0; i <= xrays; ++i, ++m)
            {
                ll_shoot_single_ray(rs->params,
                                    rect->x + i*width_per_xrays,
                                    rect->y + j*height_per_yrays,
                                    &mag_x, &mag_y);
                hit[m] = (((0 <= mag_x)     ) | ((mag_x < xpixels) << 1) |
                          ((0 <= mag_y) << 2) | ((mag_y < ypixels) << 3));
            }
        int patches = 0;
        bool *hit_patches = malloc(xrays*yrays * sizeof(bool));
        for (int j = 0, m = 0, n = 0; j < yrays; ++j, ++m)
            for (int i = 0; i < xrays; ++i, ++m, ++n)
            {
                hit_patches[n] = (hit[m] | hit[m+1] |
                                  hit[m+xrays+1] | hit[m+xrays+2]) == 15;
                patches += hit_patches[n];
            }
        free(hit);
        if (progress)
            *progress = 0.0;
        double progress_inc = 1.0 / patches;
        for (int j = 0, n = 0; j < yrays; ++j)
            for (int i = 0; i < xrays; ++i, ++n)
                if (hit_patches[n])
                {
                    double x = rect->x + i*width_per_xrays;
                    double y = rect->y + j*height_per_yrays;
                    struct ll_rect_t subrect
                        = {x, y, width_per_xrays, height_per_yrays};
                    _ll_rayshoot_recursively(rs, magpat, &subrect, rs->refine,
                                             rs->refine, level-1, 0);
                    if (progress)
                        *progress += progress_inc;
                }
        free(hit_patches);
    }
    else
        _ll_rayshoot_bilinear(rs->params, magpat, rect, rs->refine_final);
}

extern void
ll_rayshoot(struct ll_rayshooter_t *rs, int *magpat, struct ll_rect_t *rect,
            int xrays, int yrays, double *progress)
{
    rs->params->pixels_per_width = rs->params->xpixels /
        rs->params->region.width;
    rs->params->pixels_per_height = rs->params->ypixels /
        rs->params->region.height;
    _ll_rayshoot_recursively(rs, magpat, rect, xrays, yrays,
                             rs->levels - 1, progress);
}

extern void
ll_ray_hit_pattern(struct ll_magpattern_param_t *params, char *buf,
                   struct ll_rect_t *rect)
{
    double width_per_xrays = rect->width / params->xpixels;
    double height_per_yrays = rect->height / params->ypixels;
    double mag_x, mag_y;
    for (unsigned j = 0; j < params->ypixels; ++j)
        for (unsigned i = 0; i < params->xpixels; ++i)
            buf[j*params->xpixels + i] = 255 *
                ll_shoot_single_ray(params,
                                    rect->x + i*width_per_xrays,
                                    rect->y + j*height_per_yrays,
                                    &mag_x, &mag_y);
}

extern void
ll_source_images(struct ll_magpattern_param_t *params, char *buf,
                 struct ll_rect_t *rect, int xrays, int yrays, int refine,
                 double source_x, double source_y, double source_r)
{
    double r_squared = source_r*source_r;
    double width_per_xrays = rect->width / xrays;
    double height_per_yrays = rect->height / yrays;
    double x_inc = width_per_xrays / refine;
    double y_inc = height_per_yrays / refine;
    int buf_inc = 255 / (refine*refine);
    for (int j = 0, m = 0; j < xrays; ++j)
        for (int i = 0; i < yrays; ++i, ++m)
        {
            double x0 = rect->x + i*width_per_xrays;
            double y = rect->y + j*height_per_yrays;
            for (int k = 0; k < refine; ++k)
            {
                double x = x0;
                for (int l = 0; l < refine; ++l)
                {
                    double mag_x, mag_y;
                    ll_shoot_single_ray(params, x, y, &mag_x, &mag_y);
                    double dx = source_x - mag_x;
                    double dy = source_y - mag_y;
                    if (dx*dx + dy*dy < r_squared)
                        buf[m] += buf_inc;
                    x += x_inc;
                }
                y += y_inc;
            }
        }
}

extern void
ll_render_magpattern_greyscale(char *buf, int *magpat, unsigned size)
{
    int max_count = 0;
    int min_count = MAXINT;
    for(unsigned i = 0; i < size; ++i)
    {
        if (magpat[i] > max_count)
            max_count = magpat[i];
        if (magpat[i] < min_count)
            min_count = magpat[i];
    }
    if (max_count == min_count)
        return;
    double logmax = log(max_count+1);
    double logmin = log(min_count+1);
    double factor = 255/(logmax-logmin);
    for(unsigned i = 0; i < size; ++i)
        buf[i] = (log(magpat[i]+1)-logmin)*factor;
}

extern void
ll_light_curve(struct ll_magpattern_param_t *params, int *magpat,
               double *curve, unsigned num_points,
               double x0, double y0, double x1, double y1)
{
    double mag_x = (x0 - params->region.x) * params->pixels_per_width;
    double mag_y = (y0 - params->region.y) * params->pixels_per_height;
    double dx = (x1 - x0) * params->pixels_per_width / (num_points - 1);
    double dy = (y1 - y0) * params->pixels_per_height / (num_points - 1);
    for (unsigned i = 0; i < num_points; ++i)
    {
        int ix = mag_x;
        int iy = mag_y;
        int index = iy*params->xpixels + ix;
        double frac_x = mag_x - ix;
        double frac_y = mag_y - iy;
        curve[i] = (1.0 - frac_x) * (1.0 - frac_y) * magpat[index]
            + frac_x * (1.0 - frac_y) * magpat[index+1]
            + (1.0 - frac_x) * frac_y * magpat[index+params->xpixels]
            + frac_x * frac_y * magpat[index+params->xpixels+1];
        mag_x += dx;
        mag_y += dy;
    }
}
